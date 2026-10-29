from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Category, Transaction

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "password"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "user", "name", "kind", "description", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        if self.instance:
            owner = self.instance.user
        elif request and request.user.is_authenticated:
            owner = request.user
        else:
            owner = None

        name = attrs.get("name", self.instance.name if self.instance else None)
        kind = attrs.get("kind", self.instance.kind if self.instance else None)

        if (self.instance and kind != self.instance.kind and self.instance.transactions.exists()):
            raise serializers.ValidationError({
                "kind": "Tranzaksiyalari bor kategoriyaning turini o'zgartirib bo'lmaydi."
            })

        if owner is not None and name and kind:
            duplicate_categories = Category.objects.filter( user=owner, name=name, kind=kind,)
            if self.instance:
                duplicate_categories = duplicate_categories.exclude(pk=self.instance.pk)
            if duplicate_categories.exists():
                raise serializers.ValidationError({
                    "name": "Bu nom va turdagi kategoriya sizda allaqachon mavjud."
                })
        return attrs


class TransactionSerializer(serializers.ModelSerializer):

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.none())

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "category",
            "kind",
            "amount",
            "currency",
            "exchange_rate",
            "amount_uzs",
            "description",
            "transaction_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "exchange_rate",
            "amount_uzs",
            "created_at",
            "updated_at",
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if request.user.is_staff:
                fields["category"].queryset = Category.objects.all()
            else:
                fields["category"].queryset = Category.objects.filter(user=request.user)
        return fields

    def to_internal_value(self, data):
        if "amount_uzs" in data or "exchange_rate" in data:
            raise serializers.ValidationError({
                "detail": "amount_uzs va exchange_rate server tomonidan hisoblanadi; ularni yubormang."
            })
        return super().to_internal_value(data)

    def validate(self, attrs):
        instance = self.instance
        category = attrs.get("category", instance.category if instance else None)
        kind = attrs.get("kind", instance.kind if instance else None)
        amount = attrs.get("amount", instance.amount if instance else None)
        currency = attrs.get("currency", instance.currency if instance else Transaction.Currency.UZS)
        request = self.context.get("request")

        if amount is not None and amount <= Decimal("0"):
            raise serializers.ValidationError({"amount": "Summa noldan katta bo'lishi kerak."})

        if category is not None and kind is not None and category.kind != kind:
            raise serializers.ValidationError({
                "kind": "Tranzaksiya turi tanlangan kategoriya turiga mos bo'lishi kerak."
            })

        if ( category is not None and request and request.user.is_authenticated and not request.user.is_staff and category.user_id != request.user.id):
            raise serializers.ValidationError({
                "category": "Boshqa foydalanuvchining kategoriyasidan foydalanib bo'lmaydi."
            })

        if currency not in settings.CURRENCY_EXCHANGE_RATES:
            raise serializers.ValidationError({"currency": "Qo'llab-quvvatlanmaydigan valyuta."})
        return attrs

    def _calculate_conversion(self, validated_data, instance=None):
        """Valyuta kursi va UZS summasini har safar server hisoblaydi."""
        amount = validated_data.get("amount", instance.amount if instance else None)
        currency = validated_data.get("currency", instance.currency if instance else Transaction.Currency.UZS,)
        rate = Decimal(str(settings.CURRENCY_EXCHANGE_RATES[currency]))
        converted_amount = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        validated_data["exchange_rate"] = rate
        validated_data["amount_uzs"] = converted_amount

    def create(self, validated_data):
        self._calculate_conversion(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._calculate_conversion(validated_data, instance=instance)
        return super().update(instance, validated_data)

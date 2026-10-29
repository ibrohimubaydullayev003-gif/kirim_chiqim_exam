from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Category(models.Model):

    class Kind(models.TextChoices):
        INCOME = "INCOME", "Kirim"
        EXPENSE = "EXPENSE", "Chiqim"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories", verbose_name="Foydalanuvchi",)
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    kind = models.CharField(max_length=10, choices=Kind.choices, verbose_name="Turi")
    description = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        ordering = ["name", "id"]
        constraints = [models.UniqueConstraint(fields=["user", "name", "kind"], name="unique_category_name_kind_per_user",)]
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def clean(self):
        """Tranzaksiyasi bor kategoriya turini almashtirib yuborishga yo'l qo'ymaymiz."""
        super().clean()
        if self.pk:
            old_kind = Category.objects.filter(pk=self.pk).values_list("kind", flat=True).first()
            if old_kind and old_kind != self.kind and self.transactions.exists():
                raise ValidationError({"kind": "Tranzaksiyalari bor kategoriyaning turini o'zgartirib bo'lmaydi."})

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"


class Transaction(models.Model):

    class Kind(models.TextChoices):
        INCOME = "INCOME", "Kirim"
        EXPENSE = "EXPENSE", "Chiqim"

    class Currency(models.TextChoices):
        UZS = "UZS", "O'zbek so'mi"
        USD = "USD", "AQSH dollari"
        EUR = "EUR", "Yevro"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions", verbose_name="Foydalanuvchi",)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions", verbose_name="Kategoriya",)
    kind = models.CharField(max_length=10, choices=Kind.choices, verbose_name="Turi")
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Asl summa",)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.UZS, verbose_name="Valyuta",)
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=4, default=1, verbose_name="So'mga kurs",)
    amount_uzs = models.DecimalField(max_digits=22, decimal_places=2, default=0, verbose_name="So'mdagi summa",)
    description = models.TextField(blank=True, verbose_name="Izoh")
    transaction_date = models.DateField(default=timezone.localdate, verbose_name="Tranzaksiya sanasi",)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="transaction_amount_positive",)]
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"
    def clean(self):
        super().clean()
        errors = {}
        if self.amount is not None and self.amount <= Decimal("0"):
            errors["amount"] = "Summa noldan katta bo'lishi kerak."
        if self.category_id and self.kind and self.category.kind != self.kind:
            errors["kind"] = "Tranzaksiya turi kategoriya turiga mos bo'lishi kerak."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_kind_display()}: {self.amount} {self.currency}"

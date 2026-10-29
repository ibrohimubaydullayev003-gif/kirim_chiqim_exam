from calendar import monthrange
from datetime import timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from .models import Category, Transaction
from .serializers import CategorySerializer, RegisterSerializer, TransactionSerializer


@extend_schema(tags=["Autentifikatsiya"], description="Yangi oddiy foydalanuvchi yaratadi.")
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=["Kategoriyalar"])
class CategoryViewSet(viewsets.ModelViewSet):

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Category.objects.select_related("user").all()
        return Category.objects.filter(user=self.request.user).select_related("user")

    def perform_create(self, serializer):
        # user maydoni so'rovdan qabul qilinmaydi, egani token belgilaydi.
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        try:
            category.delete()
        except ProtectedError:
            return Response({"detail": "Bu kategoriyada tranzaksiyalar bor. Avval tranzaksiyalarni o'chiring yoki boshqa kategoriya tanlang."}, status=status.HTTP_400_BAD_REQUEST,)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Tranzaksiyalar"])
class TransactionViewSet(viewsets.ModelViewSet):

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = Transaction.objects.select_related("category", "user").all()
        else:
            queryset = Transaction.objects.filter(user=self.request.user).select_related("category", "user")

        query_params = self.request.query_params
        kind = query_params.get("kind")
        currency = query_params.get("currency")
        date_from_text = query_params.get("date_from")
        date_to_text = query_params.get("date_to")

        valid_kinds = [choice[0] for choice in Transaction.Kind.choices]
        valid_currencies = [choice[0] for choice in Transaction.Currency.choices]

        if kind:
            if kind not in valid_kinds:
                raise ValidationError({"kind": "kind INCOME yoki EXPENSE bo'lishi kerak."})
            queryset = queryset.filter(kind=kind)

        if currency:
            if currency not in valid_currencies:
                raise ValidationError({"currency": "currency UZS, USD yoki EUR bo'lishi kerak."})
            queryset = queryset.filter(currency=currency)

        if date_from_text:
            date_from = parse_date(date_from_text)
            if date_from is None:
                raise ValidationError({"date_from": "Sana YYYY-MM-DD formatida bo'lishi kerak."})
            queryset = queryset.filter(transaction_date__gte=date_from)

        if date_to_text:
            date_to = parse_date(date_to_text)
            if date_to is None:
                raise ValidationError({"date_to": "Sana YYYY-MM-DD formatida bo'lishi kerak."})
            queryset = queryset.filter(transaction_date__lte=date_to)

        if date_from_text and date_to_text and date_from > date_to:
            raise ValidationError({"date_range": "date_from sanasi date_to sanasidan keyin bo'lmasligi kerak."})

        return queryset.order_by("-transaction_date", "-created_at")

    def perform_create(self, serializer)
        serializer.save(user=self.request.user)


class BaseReportView(APIView):

    permission_classes = [IsAuthenticated]
    period_name = "daily"

    @extend_schema(
        tags=["Hisobotlar"],
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Hisobot uchun sana (YYYY-MM-DD). Berilmasa, bugungi sana olinadi.",
            )
        ],
        description="Jami kirim/chiqimni, balansni va kategoriya kesimidagi statistikani UZS da qaytaradi.",
    )
    def get(self, request):
        reference_date = self.get_reference_date(request)
        period_start, period_end = self.get_period_dates(reference_date)

        transactions = Transaction.objects.filter(transaction_date__range=(period_start, period_end)).select_related("category")
        if not request.user.is_staff:
            transactions = transactions.filter(user=request.user)

        income_total = transactions.filter(kind=Transaction.Kind.INCOME).aggregate(total=Sum("amount_uzs"))["total"] or Decimal("0.00")
        expense_total = transactions.filter(kind=Transaction.Kind.EXPENSE).aggregate(total=Sum("amount_uzs"))["total"] or Decimal("0.00")
        income_total = income_total.quantize(Decimal("0.01"))
        expense_total = expense_total.quantize(Decimal("0.01"))
        balance = (income_total - expense_total).quantize(Decimal("0.01"))

        grouped_rows = transactions.values("category__name", "kind").annotate(total=Sum("amount_uzs"), count=Count("id"),).order_by("category__name", "kind")

        by_category = []
        for row in grouped_rows:
            by_category.append({
                "category": row["category__name"],
                "kind": row["kind"],
                "total": self.format_money(row["total"] or Decimal("0.00")),
                "count": row["count"],
            })

        income_by_category = [row for row in by_category if row["kind"] == Transaction.Kind.INCOME]
        expense_by_category = [row for row in by_category if row["kind"] == Transaction.Kind.EXPENSE]

        response_data = {
            "period": self.period_name,
            "currency": "UZS",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_income": self.format_money(income_total),
            "total_expense": self.format_money(expense_total),
            "balance": self.format_money(balance),
            "transaction_count": transactions.count(),
            "income_by_category": income_by_category,
            "expense_by_category": expense_by_category,
            "by_category": by_category,
        }
        return Response(response_data)

    @staticmethod
    def format_money(value):
        return format(Decimal(value).quantize(Decimal("0.01")), ".2f")

    def get_reference_date(self, request):
        date_text = request.query_params.get("date")
        if not date_text:
            return timezone.localdate()
        selected_date = parse_date(date_text)
        if selected_date is None:
            raise ValidationError({"date": "Sana YYYY-MM-DD formatida bo'lishi kerak."})
        return selected_date

    def get_period_dates(self, reference_date):
        if self.period_name == "daily":
            return reference_date, reference_date

        if self.period_name == "weekly":
            start_date = reference_date - timedelta(days=reference_date.weekday())
            return start_date, start_date + timedelta(days=6)

        start_date = reference_date.replace(day=1)
        end_date = reference_date.replace(day=monthrange(reference_date.year, reference_date.month)[1])
        return start_date, end_date


@extend_schema(tags=["Hisobotlar"])
class DailyReportView(BaseReportView):
    period_name = "daily"


@extend_schema(tags=["Hisobotlar"])
class WeeklyReportView(BaseReportView):
    period_name = "weekly"


@extend_schema(tags=["Hisobotlar"])
class MonthlyReportView(BaseReportView):
    period_name = "monthly"

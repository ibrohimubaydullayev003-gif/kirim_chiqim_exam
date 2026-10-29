from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "kind", "user", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("name", "user__username", "user__email")
    readonly_fields = ("created_at",)
    list_select_related = ("user",)

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.transactions.exists():
            fields.extend(["kind", "user"])
        return tuple(fields)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "transaction_date",
        "user",
        "category",
        "kind",
        "amount",
        "currency",
        "amount_uzs",
    )
    list_filter = ("kind", "currency", "transaction_date", "category")
    search_fields = ("description", "user__username", "category__name")
    readonly_fields = ("exchange_rate", "amount_uzs", "created_at", "updated_at")
    date_hierarchy = "transaction_date"
    list_select_related = ("user", "category")

    def save_model(self, request, obj, form, change):
        # Admin paneldan summa yoki valyuta o'zgarsa ham UZS summasini qayta hisoblaymiz.
        rate = Decimal(str(settings.CURRENCY_EXCHANGE_RATES[obj.currency]))
        obj.exchange_rate = rate
        obj.amount_uzs = (obj.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # Admin orqali saqlashda ham modelning tekshiruvlarini bajaramiz.
        obj.full_clean()
        super().save_model(request, obj, form, change)

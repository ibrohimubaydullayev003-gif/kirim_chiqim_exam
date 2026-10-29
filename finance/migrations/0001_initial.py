# Ushbu dastlabki migratsiya Category va Transaction jadvallarini yaratadi.
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Kategoriya nomi")),
                ("kind", models.CharField(choices=[("INCOME", "Kirim"), ("EXPENSE", "Chiqim")], max_length=10, verbose_name="Turi")),
                ("description", models.TextField(blank=True, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categories", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Kategoriya",
                "verbose_name_plural": "Kategoriyalar",
                "ordering": ["name", "id"],
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("INCOME", "Kirim"), ("EXPENSE", "Chiqim")], max_length=10, verbose_name="Turi")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Asl summa")),
                ("currency", models.CharField(choices=[("UZS", "O'zbek so'mi"), ("USD", "AQSH dollari"), ("EUR", "Yevro")], default="UZS", max_length=3, verbose_name="Valyuta")),
                ("exchange_rate", models.DecimalField(decimal_places=4, default=1, max_digits=14, verbose_name="So'mga kurs")),
                ("amount_uzs", models.DecimalField(decimal_places=2, default=0, max_digits=22, verbose_name="So'mdagi summa")),
                ("description", models.TextField(blank=True, verbose_name="Izoh")),
                ("transaction_date", models.DateField(default=django.utils.timezone.localdate, verbose_name="Tranzaksiya sanasi")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="finance.category", verbose_name="Kategoriya")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Tranzaksiya",
                "verbose_name_plural": "Tranzaksiyalar",
                "ordering": ["-transaction_date", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(fields=("user", "name", "kind"), name="unique_category_name_kind_per_user"),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name="transaction_amount_positive"),
        ),
    ]

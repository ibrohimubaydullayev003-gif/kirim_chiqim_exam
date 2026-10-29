from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, DailyReportView, MonthlyReportView, TransactionViewSet, WeeklyReportView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("reports/daily/", DailyReportView.as_view(), name="report-daily"),
    path("reports/weekly/", WeeklyReportView.as_view(), name="report-weekly"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="report-monthly"),
]

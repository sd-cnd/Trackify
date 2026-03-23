from django.urls import path
from .views import MonthlyAttendanceView

urlpatterns = [
    path("monthly/", MonthlyAttendanceView.as_view(), name="monthly-attendance"),
]
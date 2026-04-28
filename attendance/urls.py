from django.urls import path
from .views import MonthlyAttendanceView, AttendanceCreateView

urlpatterns = [
    path("monthly/", MonthlyAttendanceView.as_view(), name="monthly-attendance"),
    path("create/", AttendanceCreateView.as_view(), name="attendance-create"),
]
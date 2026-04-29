from django.urls import path
from .views import (
    ApplyLeaveView,
    MyLeavesView,
    ApproveLeaveView,
    LeaveBalanceView,
    TeamLeavesView,
    TodayOnLeaveView,
    MonthlyCalendarView,
)

urlpatterns = [
    path("apply/", ApplyLeaveView.as_view(), name="leave-apply"),
    path("my/", MyLeavesView.as_view(), name="leave-my"),
    path("<int:pk>/action/", ApproveLeaveView.as_view(), name="leave-action"),
    path("balance/", LeaveBalanceView.as_view(), name="leave-balance"),
    path("team/", TeamLeavesView.as_view(), name="leave-team"),
    path("today/", TodayOnLeaveView.as_view(), name="leave-today"),
    path("calendar/", MonthlyCalendarView.as_view(), name="leave-calendar"),
]
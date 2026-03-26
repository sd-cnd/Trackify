from django.urls import path
from .views import (
    ApplyLeaveView,
    MyLeavesView,
    ApproveLeaveView,
    LeaveBalanceView,
    TeamLeavesView,
    TodayOnLeaveView,
    MonthlyCalendarView
)

urlpatterns = [
    path("apply/", ApplyLeaveView.as_view()),
    path("my/", MyLeavesView.as_view()),
    path("<int:pk>/action/", ApproveLeaveView.as_view()),

    # NEW APIs
    path("balance/", LeaveBalanceView.as_view()),
    path("team/", TeamLeavesView.as_view()),
    path("today/", TodayOnLeaveView.as_view()),
    path("calendar/", MonthlyCalendarView.as_view()),
]

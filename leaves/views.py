from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import date
import calendar

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Leave, LeaveQuota
from accounts.models import Employee
from projects.models import ProjectMembership


# -----------------------------
# Swagger Serializers
# -----------------------------

class ApplyLeaveSerializer(serializers.Serializer):
    leave_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class ApproveLeaveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVED", "REJECTED"])


# -----------------------------
# APPLY LEAVE
# -----------------------------
class ApplyLeaveView(APIView):

    @swagger_auto_schema(
        request_body=ApplyLeaveSerializer,
        responses={200: "Leave applied successfully"}
    )
    def post(self, request):
        user = request.user

        leave = Leave(
            employee=user,
            leave_type=request.data.get("leave_type"),
            start_date=request.data.get("start_date"),
            end_date=request.data.get("end_date"),
        )

        leave.save()

        return Response({"message": "Leave applied successfully"})


# -----------------------------
# MY LEAVES
# -----------------------------
class MyLeavesView(APIView):

    def get(self, request):
        leaves = Leave.objects.filter(employee=request.user)

        data = [
            {
                "id": l.id,
                "type": l.leave_type,
                "start": l.start_date,
                "end": l.end_date,
                "status": l.status,
            }
            for l in leaves
        ]

        return Response(data)


# -----------------------------
# APPROVE / REJECT
# -----------------------------
class ApproveLeaveView(APIView):

    @swagger_auto_schema(
        request_body=ApproveLeaveSerializer,
        responses={
            200: "Leave approved/rejected successfully",
            400: "Invalid action",
            403: "Not authorized"
        }
    )
    def patch(self, request, pk):
        user = request.user

        leave = get_object_or_404(Leave, pk=pk)

        action = request.data.get("action")

        if action not in ["APPROVED", "REJECTED"]:
            return Response({"error": "Invalid action"}, status=400)

        if not self.can_approve(user, leave):
            return Response({"error": "Not authorized"}, status=403)

        leave.status = action
        leave.approved_by = user
        leave.save()

        return Response({"message": f"Leave {action.lower()} successfully"})

    def can_approve(self, user, leave):
        if user.role == "GLOBAL_HR":
            return True

        if user.role == "PROJECT_HR":
            if leave.employee.role in ["PROJECT_HR", "GLOBAL_HR"]:
                return False

            return ProjectMembership.objects.filter(
                employee=leave.employee,
                project__hr=user,
                end_date__isnull=True
            ).exists()

        return False


# -----------------------------
# LEAVE BALANCE API
# -----------------------------
class LeaveBalanceView(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Year to fetch leave balance for (default: current year)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: "Leave balance data", 404: "Quota not found"}
    )
    def get(self, request):
        user = request.user
        year = request.query_params.get("year", date.today().year)

        quota = LeaveQuota.objects.filter(
            employee=user,
            year=year
        ).first()

        if not quota:
            return Response({"error": "Quota not found"}, status=404)

        data = {
            "EL": {
                "total": quota.el_quota,
                "taken": quota.el_taken,
                "remaining": quota.el_quota - quota.el_taken
            },
            "CL": {
                "total": quota.cl_quota,
                "taken": quota.cl_taken,
                "remaining": quota.cl_quota - quota.cl_taken
            },
            "SL": {
                "total": quota.sl_quota,
                "taken": quota.sl_taken,
                "remaining": quota.sl_quota - quota.sl_taken
            },
            "OL": {
                "total": quota.ol_quota,
                "taken": quota.ol_taken,
                "remaining": quota.ol_quota - quota.ol_taken
            }
        }

        return Response(data)


# -----------------------------
# TEAM LEAVES (HR VIEW)
# -----------------------------
class TeamLeavesView(APIView):

    def get(self, request):
        user = request.user

        if user.role == "GLOBAL_HR":
            leaves = Leave.objects.all()

        elif user.role == "PROJECT_HR":
            employee_ids = ProjectMembership.objects.filter(
                project__hr=user,
                end_date__isnull=True
            ).values_list("employee_id", flat=True)

            leaves = Leave.objects.filter(employee_id__in=employee_ids)

        else:
            return Response({"error": "Not authorized"}, status=403)

        data = [
            {
                "employee": l.employee.name,
                "type": l.leave_type,
                "start": l.start_date,
                "end": l.end_date,
                "status": l.status,
            }
            for l in leaves
        ]

        return Response(data)


# -----------------------------
# WHO IS ON LEAVE TODAY
# -----------------------------
class TodayOnLeaveView(APIView):

    def get(self, request):
        user = request.user
        today = date.today()

        leaves = Leave.objects.filter(
            status="APPROVED",
            start_date__lte=today,
            end_date__gte=today
        )

        if user.role == "GLOBAL_HR":
            pass

        elif user.role == "PROJECT_HR":
            employee_ids = ProjectMembership.objects.filter(
                project__hr=user,
                end_date__isnull=True
            ).values_list("employee_id", flat=True)

            leaves = leaves.filter(employee_id__in=employee_ids)

        else:
            leaves = leaves.filter(employee=user)

        data = [
            {
                "employee": l.employee.name,
                "leave_type": l.leave_type,
                "from": l.start_date,
                "to": l.end_date,
            }
            for l in leaves
        ]

        return Response(data)


# -----------------------------
# MONTHLY CALENDAR
# -----------------------------
class MonthlyCalendarView(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="Month number (1-12, default: current month)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Year (default: current year)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: "Monthly calendar with leave data"}
    )
    def get(self, request):
        user = request.user

        month = int(request.query_params.get("month", date.today().month))
        year = int(request.query_params.get("year", date.today().year))

        _, num_days = calendar.monthrange(year, month)

        leaves = Leave.objects.filter(
            status="APPROVED",
            start_date__lte=date(year, month, num_days),
            end_date__gte=date(year, month, 1)
        )

        if user.role == "GLOBAL_HR":
            pass

        elif user.role == "PROJECT_HR":
            employee_ids = ProjectMembership.objects.filter(
                project__hr=user,
                end_date__isnull=True
            ).values_list("employee_id", flat=True)

            leaves = leaves.filter(employee_id__in=employee_ids)

        else:
            leaves = leaves.filter(employee=user)

        calendar_data = {}

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)

            day_leaves = leaves.filter(
                start_date__lte=current_date,
                end_date__gte=current_date
            )

            calendar_data[str(current_date)] = [
                {
                    "employee": l.employee.name,
                    "leave_type": l.leave_type
                }
                for l in day_leaves
            ]

        return Response({
            "month": month,
            "year": year,
            "calendar": calendar_data
        })
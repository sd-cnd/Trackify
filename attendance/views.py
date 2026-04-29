from datetime import date
import calendar

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Attendance
from .serializers import AttendanceSerializer
from accounts.models import Employee
from organization.models import Holiday
from leaves.models import Leave
from projects.models import ProjectMembership


class MonthlyAttendanceView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'employee',
                openapi.IN_QUERY,
                description="Employee ID (required)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="Month number (1-12)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Year (e.g. 2024)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: "Monthly attendance data",
            400: "Invalid month/year or missing employee",
            403: "Not allowed",
            404: "Invalid employee"
        }
    )
    def get(self, request):

        user = request.user
        employee_id = request.GET.get("employee")

        if not employee_id:
            return Response({"error": "employee is required"}, status=400)

        try:
            month = int(request.GET.get("month"))
            year = int(request.GET.get("year"))

            if month < 1 or month > 12:
                return Response({"error": "Invalid month"}, status=400)

        except (TypeError, ValueError):
            return Response({"error": "Invalid month/year"}, status=400)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Invalid employee"}, status=404)

        # 🔐 ROLE-BASED ACCESS

        if user.role == "EMPLOYEE":
            if user.id != employee.id:
                return Response({"error": "Not allowed"}, status=403)

        elif user.role == "PROJECT_HR":
            hr_projects = ProjectMembership.objects.filter(
                employee=user
            ).values_list("project_id", flat=True)

            is_allowed = ProjectMembership.objects.filter(
                employee=employee,
                project_id__in=hr_projects
            ).exists()

            if not is_allowed:
                return Response({"error": "Not allowed"}, status=403)

        elif user.role == "GLOBAL_HR":
            pass
        else:
            return Response({"error": "Role not supported"}, status=403)

        num_days = calendar.monthrange(year, month)[1]

        attendance_qs = Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )

        attendance_map = {att.date: att for att in attendance_qs}

        result = []

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)

            if current_date in attendance_map:
                att = attendance_map[current_date]
                result.append({
                    "date": current_date,
                    "status": att.status,
                    "check_in": att.check_in_time,
                    "check_out": att.check_out_time,
                })
            else:
                if Holiday.objects.filter(date=current_date).exists():
                    status_val = "HOLIDAY"

                elif Leave.objects.filter(
                    employee=employee,
                    status="APPROVED",
                    start_date__lte=current_date,
                    end_date__gte=current_date
                ).exists():
                    status_val = "LEAVE"

                else:
                    status_val = "ABSENT"

                result.append({
                    "date": current_date,
                    "status": status_val,
                    "check_in": None,
                    "check_out": None,
                })

        return Response(result, status=status.HTTP_200_OK)


# ✅ FIXED CREATE API
class AttendanceCreateView(CreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        employee_id = request.data.get("employee")

        if not employee_id:
            return Response({"error": "employee is required"}, status=400)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Invalid employee"}, status=404)

        # 🔐 ROLE-BASED ACCESS

        if user.role == "EMPLOYEE":
            if user.id != employee.id:
                return Response({"error": "Not allowed"}, status=403)

        elif user.role == "PROJECT_HR":
            hr_projects = ProjectMembership.objects.filter(
                employee=user
            ).values_list("project_id", flat=True)

            is_allowed = ProjectMembership.objects.filter(
                employee=employee,
                project_id__in=hr_projects
            ).exists()

            if not is_allowed:
                return Response({"error": "Not allowed"}, status=403)

        elif user.role == "GLOBAL_HR":
            pass
        else:
            return Response({"error": "Role not supported"}, status=403)

        # ✅ normal DRF flow
        return super().create(request, *args, **kwargs)
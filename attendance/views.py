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
        operation_summary="Get Monthly Attendance",
        operation_description="Returns day-by-day attendance status for an employee for a given month and year. Status can be PRESENT, ABSENT, LEAVE, or HOLIDAY. Access is role-based: EMPLOYEE can only view their own, PROJECT_HR can view employees in their projects, GLOBAL_HR can view all.",
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
                description="Month number between 1 and 12 (required)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Year e.g. 2024 (required)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(description="Monthly attendance data returned successfully."),
            400: openapi.Response(description="Bad Request. Employee ID, month, or year is missing or invalid."),
            403: openapi.Response(description="Forbidden. You do not have permission to view this employee's attendance."),
            404: openapi.Response(description="Not Found. Employee does not exist."),
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


class AttendanceCreateView(CreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Mark Attendance",
        operation_description="Mark attendance for an employee. EMPLOYEE can only mark their own attendance. PROJECT_HR can mark for employees in their projects. GLOBAL_HR can mark for anyone.",
        responses={
            201: openapi.Response(description="Attendance marked successfully."),
            400: openapi.Response(description="Bad Request. Employee ID is missing or attendance already marked for this date."),
            403: openapi.Response(description="Forbidden. You do not have permission to mark attendance for this employee."),
            404: openapi.Response(description="Not Found. Employee does not exist."),
        }
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        employee_id = request.data.get("employee")

        if not employee_id:
            return Response({"error": "employee is required"}, status=400)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Invalid employee"}, status=404)

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

        return super().create(request, *args, **kwargs)
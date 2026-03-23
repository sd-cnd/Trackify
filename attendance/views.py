from datetime import date
import calendar

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Attendance
from accounts.models import Employee
from organization.models import Holiday
from leaves.models import Leave
from projects.models import ProjectMembership


class MonthlyAttendanceView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user  # logged-in employee

        employee_id = request.GET.get("employee")
        month = int(request.GET.get("month"))
        year = int(request.GET.get("year"))

        if not employee_id:
            return Response({"error": "employee is required"}, status=400)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Invalid employee"}, status=404)

        # 🔐 ROLE-BASED ACCESS CONTROL

        # EMPLOYEE → only self
        if user.role == "EMPLOYEE":
            if user.id != employee.id:
                return Response({"error": "Not allowed"}, status=403)

        # PROJECT_HR → only employees in their projects
        elif user.role == "PROJECT_HR":

            # Get projects where this HR is a member
            hr_projects = ProjectMembership.objects.filter(
                employee=user
            ).values_list("project_id", flat=True)

            # Check if target employee is in any of those projects
            is_allowed = ProjectMembership.objects.filter(
                employee=employee,
                project_id__in=hr_projects
            ).exists()

            if not is_allowed:
                return Response({"error": "Not allowed"}, status=403)

        # GLOBAL_HR → full access
        elif user.role == "GLOBAL_HR":
            pass

        # (Optional) SUPERVISOR → restrict later
        else:
            return Response({"error": "Role not supported"}, status=403)

        # 📅 MONTH CALCULATION
        num_days = calendar.monthrange(year, month)[1]

        # 📊 FETCH ATTENDANCE
        attendance_qs = Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )

        attendance_map = {
            att.date: att for att in attendance_qs
        }

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
                # Holiday check
                if Holiday.objects.filter(date=current_date).exists():
                    status_val = "HOLIDAY"

                # Leave check
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
from datetime import date, time
from unittest.mock import patch
from urllib import response

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import Employee
from projects.models import Project, ProjectMembership
from organization.models import Holiday

from .models import Attendance
from .serializers import AttendanceSerializer


# =========================
#      MODEL TESTS
# =========================
class AttendanceModelTest(TestCase):

    def setUp(self):
        self.employee = Employee.objects.create_user(
            email="emp@test.com",
            name="Test Employee",
            password="pass123",
            role="EMPLOYEE"
        )

        self.project = Project.objects.create(
            project_name="Test Project",
            project_type="BILLABLE",
            created_by=self.employee
        )

    def test_create_attendance_success(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 1),
            status="PRESENT",
            check_in_time=time(9, 0),
            check_out_time=time(17, 0)
        )
        self.assertEqual(attendance.status, "PRESENT")

    def test_unique_constraint(self):
        Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 2),
            status="PRESENT"
        )

        with self.assertRaises(Exception):
            Attendance.objects.create(
                employee=self.employee,
                project=self.project,
                date=date(2026, 4, 2),
                status="ABSENT"
            )

    def test_holiday_validation(self):
        Holiday.objects.create(date=date(2026, 4, 3))

        with self.assertRaises(Exception):
            Attendance.objects.create(
                employee=self.employee,
                project=self.project,
                date=date(2026, 4, 3),
                status="PRESENT"
            )

    @patch("attendance.utils.Leave.objects.filter")
    def test_leave_validation(self, mock_leave_filter):
        mock_leave_filter.return_value.exists.return_value = True

        with self.assertRaises(Exception):
            Attendance.objects.create(
                employee=self.employee,
                project=self.project,
                date=date(2026, 4, 5),
                status="PRESENT"
            )

    # Multiple projects same day
    def test_multiple_projects_same_day(self):
        project2 = Project.objects.create(
            project_name="P2",
            project_type="BILLABLE",
            created_by=self.employee
        )

        Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 1),
            status="PRESENT"
        )

        with self.assertRaises(Exception):
            Attendance.objects.create(
                employee=self.employee,
                project=project2,
                date=date(2026, 4, 1),
                status="PRESENT"
            )

    # Partial time allowed
    def test_only_checkin_without_checkout(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 1),
            status="PRESENT",
            check_in_time=time(9, 0)
        )

        self.assertIsNotNone(attendance)


# =========================
#       API TESTS
# =========================
class MonthlyAttendanceAPITest(APITestCase):

    def setUp(self):
        self.employee = Employee.objects.create_user(
            email="emp1@test.com",
            name="Employee",
            password="pass123",
            role="EMPLOYEE"
        )

        self.hr = Employee.objects.create_user(
            email="hr@test.com",
            name="HR",
            password="pass123",
            role="PROJECT_HR"
        )

        self.global_hr = Employee.objects.create_user(
            email="global@test.com",
            name="Global HR",
            password="pass123",
            role="GLOBAL_HR"
        )

        self.project = Project.objects.create(
            project_name="Test Project",
            project_type="BILLABLE",
            created_by=self.global_hr,
            hr=self.hr
        )

        ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date=date(2026, 1, 1)
        )

        ProjectMembership.objects.create(
            employee=self.hr,
            project=self.project,
            role="HR",
            start_date=date(2026, 1, 1)
        )

        Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 1),
            status="PRESENT"
        )

        self.url = reverse("monthly-attendance")

    def test_employee_can_view_own_attendance(self):
        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 4,
            "year": 2026
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_view_others(self):
        other = Employee.objects.create_user(
            email="other@test.com",
            name="Other",
            password="pass123",
            role="EMPLOYEE"
        )

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": other.id,
            "month": 4,
            "year": 2026
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_hr_can_view_project_employee(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 4,
            "year": 2026
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_hr_cannot_view_outside_employee(self):
        outsider = Employee.objects.create_user(
            email="outsider@test.com",
            name="Outsider",
            password="pass123",
            role="EMPLOYEE"
        )

        self.client.force_authenticate(user=self.hr)

        response = self.client.get(self.url, {
            "employee": outsider.id,
            "month": 4,
            "year": 2026
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_global_hr_has_full_access(self):
        outsider = Employee.objects.create_user(
            email="outsider2@test.com",
            name="Outsider",
            password="pass123",
            role="EMPLOYEE"
        )

        self.client.force_authenticate(user=self.global_hr)

        response = self.client.get(self.url, {
            "employee": outsider.id,
            "month": 4,
            "year": 2026
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_holiday_reflected_in_response(self):
        Holiday.objects.create(date=date(2026, 4, 10))

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 4,
            "year": 2026
        })

        holiday_entry = next(d for d in response.data if d["date"].day == 10)
        self.assertEqual(holiday_entry["status"], "HOLIDAY")

    @patch("attendance.views.Leave.objects.filter")
    def test_leave_reflected_in_response(self, mock_leave_filter):
        mock_leave_filter.return_value.exists.return_value = True

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 4,
            "year": 2026
        })

        leave_entry = next(d for d in response.data if d["date"].day == 15)
        self.assertEqual(leave_entry["status"], "LEAVE")

    # Last day boundary
    def test_last_day_of_month(self):
        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 2,
            "year": 2026
        })

        self.assertEqual(len(response.data), 28)

    # No attendance month
    def test_no_attendance_month(self):
        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url, {
            "employee": self.employee.id,
            "month": 5,
            "year": 2026
        })

        self.assertTrue(all(d["status"] == "ABSENT" for d in response.data))

    @patch("attendance.views.Leave.objects.filter")
    def test_attendance_overrides_leave(self, mock_leave_filter):

        # simulate leave exists
        mock_leave_filter.return_value.exists.return_value = True

        self.client.force_authenticate(user=self.employee)

        url = reverse("attendance-create")

        response = self.client.post(url, {
            "employee": self.employee.id,
            "project": self.project.id,
            "date": "2026-04-25",
            "status": "PRESENT"
        })

        # EXPECTATION: API handles override logic, not model
        self.assertEqual(response.status_code, 400)


class MonthlyAttendanceInvalidInputTest(APITestCase):

    def setUp(self):
        self.user = Employee.objects.create_user(
            email="test@test.com",
            name="Test",
            password="pass123",
            role="GLOBAL_HR"
        )
        self.url = reverse("monthly-attendance")
        self.client.force_authenticate(user=self.user)

    def test_missing_employee_param(self):
        response = self.client.get(self.url, {
            "month": 4,
            "year": 2026
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_employee(self):
        response = self.client.get(self.url, {
            "employee": 999,
            "month": 4,
            "year": 2026
        })
        self.assertEqual(response.status_code, 404)

    def test_invalid_month(self):
        response = self.client.get(self.url, {
            "employee": self.user.id,
            "month": 13,
            "year": 2026
        })
        self.assertEqual(response.status_code, 400)

    def test_missing_month(self):
        response = self.client.get(self.url, {
            "employee": self.user.id,
            "year": 2026
        })
        self.assertEqual(response.status_code, 400)

    def test_missing_year(self):
        response = self.client.get(self.url, {
            "employee": self.user.id,
            "month": 4
        })
        self.assertEqual(response.status_code, 400)


class AttendanceCreateAPITest(APITestCase):

    def setUp(self):
        self.employee = Employee.objects.create_user(
            email="emp@test.com",
            name="Emp",
            password="pass123",
            role="EMPLOYEE"
        )

        self.project = Project.objects.create(
            project_name="Test",
            project_type="BILLABLE",
            created_by=self.employee
        )

        self.client.force_authenticate(user=self.employee)
        self.url = reverse("attendance-create")

    def test_mark_attendance_success(self):
        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "date": "2026-04-01",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_attendance_fails(self):
        Attendance.objects.create(
            employee=self.employee,
            project=self.project,
            date=date(2026, 4, 1),
            status="PRESENT"
        )

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "date": "2026-04-01",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    # Unauthorized marking
    def test_employee_cannot_mark_others_attendance(self):
        other = Employee.objects.create_user(
            email="other@test.com",
            name="Other",
            password="pass123",
            role="EMPLOYEE"
        )

        data = {
            "employee": other.id,
            "project": self.project.id,
            "date": "2026-04-01",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)

    # Missing fields
    def test_missing_fields_should_fail(self):
        response = self.client.post(self.url, {
            "employee": self.employee.id
        })

        self.assertEqual(response.status_code, 400)

    # Invalid project
    def test_invalid_project_should_fail(self):
        data = {
            "employee": self.employee.id,
            "project": 999,
            "date": "2026-04-01",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    
    def test_create_missing_employee(self):
        data = {
            "project": self.project.id,
            "date": "2026-04-02",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)

    def test_create_invalid_employee(self):
        data = {
            "employee": 999,
            "project": self.project.id,
            "date": "2026-04-02",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 404)

    def test_cannot_mark_on_holiday(self):
        Holiday.objects.create(date=date(2026, 4, 3))

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "date": "2026-04-03",
            "status": "PRESENT"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)

    
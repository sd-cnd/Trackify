from django.test import TestCase
from datetime import date, timedelta
import uuid
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from accounts.models import Employee
from projects.models import Project, ProjectMembership
from leaves.models import Leave, LeaveQuota


# -----------------------------
# Helper
# -----------------------------
def create_employee(name):
    return Employee.objects.create(
        name=name,
        email=f"{name}_{uuid.uuid4().hex[:6]}@test.com"
    )


class BaseTestSetup(TestCase):

    def setUp(self):

        # Employees
        self.hr_user = create_employee("hr")
        self.manager_user = create_employee("manager")
        self.employee_user = create_employee("employee")

        # Project
        self.project = Project.objects.create(
            project_name="Trackify Project",
            project_type="BILLABLE",
            supervisor=self.manager_user,
            hr=self.hr_user,
            created_by=self.hr_user,
            is_active=True
        )

        ProjectMembership.objects.create(
            employee=self.employee_user,
            project=self.project,
            role="MEMBER",
            start_date=date.today()
        )

        # Leave Quota
        self.quota = LeaveQuota.objects.create(
            employee=self.employee_user,
            year=date.today().year,
            el_quota=12,
            cl_quota=10,
            sl_quota=8,
            ol_quota=2,
            el_taken=0,
            cl_taken=0,
            sl_taken=0,
            ol_taken=0
        )


# -----------------------------
# Leave Model Tests
# -----------------------------
class LeaveModelTests(BaseTestSetup):

    def test_duration(self):
        leave = Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPLIED"
        )

        self.assertEqual(leave.get_duration(), 3)

    def test_invalid_date_range(self):
        leave = Leave(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),
            status="APPLIED"
        )

        with self.assertRaises(ValidationError):
            leave.full_clean()

    def test_overlapping_leave(self):
        Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPLIED"
        )

        with self.assertRaises(ValidationError):
            Leave.objects.create(
                employee=self.employee_user,
                leave_type="EL",
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=3),
                status="APPLIED"
            )

    def test_quota_missing(self):
        LeaveQuota.objects.all().delete()

        leave = Leave(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today(),
            status="APPROVED"
        )

        with self.assertRaises(ValidationError):
            leave.full_clean()

    def test_leave_rejected_when_quota_exceeded(self):

        LeaveQuota.objects.filter(employee=self.employee_user).delete()

        LeaveQuota.objects.create(
            employee=self.employee_user,
            year=date.today().year,
            el_quota=2,
            el_taken=0
        )

        leave = Leave(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            status="APPROVED"
        )

        with self.assertRaises(ValidationError):
            leave.full_clean()

    def test_quota_not_applied_for_applied_leave(self):
        leave = Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPLIED"
        )

        self.quota.refresh_from_db()
        self.assertEqual(self.quota.el_taken, 0)

    def test_quota_not_doubled_on_multiple_saves(self):
        leave = Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPROVED"
        )

        leave.status = "APPROVED"
        leave.save()

        self.quota.refresh_from_db()
        self.assertEqual(self.quota.el_taken, 3)

    def test_quota_reverts_when_leave_rejected(self):
        leave = Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPROVED"
        )

        leave.status = "REJECTED"
        leave.save()

        self.quota.refresh_from_db()
        self.assertEqual(self.quota.el_taken, 0)

    def test_invalid_leave_type_fails(self):
        with self.assertRaises(Exception):
            Leave.objects.create(
                employee=self.employee_user,
                leave_type="XYZ",
                start_date=date.today(),
                end_date=date.today(),
                status="APPROVED"
            )

    def test_touching_dates_are_allowed(self):
        Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPROVED"
        )

        leave2 = Leave(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today() + timedelta(days=3),
            end_date=date.today() + timedelta(days=4),
            status="APPROVED"
        )

        leave2.full_clean()

    def test_exact_overlap_rejected(self):
        Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            status="APPROVED"
        )

        leave = Leave(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=5),
            status="APPROVED"
        )

        with self.assertRaises(ValidationError):
            leave.full_clean()


# -----------------------------
# Approval Tests
# -----------------------------
class LeaveApprovalTests(BaseTestSetup):

    def test_apply_quota_on_approval(self):
        leave = Leave.objects.create(
            employee=self.employee_user,
            leave_type="EL",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            status="APPROVED"
        )

        self.quota.refresh_from_db()
        self.assertEqual(self.quota.el_taken, 3)


# -----------------------------
# LeaveQuota Tests
# -----------------------------
class LeaveQuotaModelTests(BaseTestSetup):

    def test_unique_quota_per_year(self):

        LeaveQuota.objects.filter(employee=self.employee_user).delete()

        LeaveQuota.objects.create(
            employee=self.employee_user,
            year=date.today().year
        )

        with self.assertRaises(IntegrityError):
            LeaveQuota.objects.create(
                employee=self.employee_user,
                year=date.today().year
            )

    def test_default_quota_values(self):

        LeaveQuota.objects.filter(employee=self.employee_user).delete()

        quota = LeaveQuota.objects.create(
            employee=self.employee_user,
            year=date.today().year
        )

        self.assertEqual(quota.el_quota, 12)
        self.assertEqual(quota.cl_quota, 10)
        self.assertEqual(quota.sl_quota, 8)
        self.assertEqual(quota.ol_quota, 2)
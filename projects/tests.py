from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import Employee
from .models import Project, ProjectMembership
from django.urls import reverse
from django.db import IntegrityError, transaction


class ProjectMembershipTests(APITestCase):

    def setUp(self):
        self.global_hr = Employee.objects.create_user(
            email="global@example.com",
            name="Global HR",
            password="pass123",
            role="GLOBAL_HR"
        )

        self.project_hr = Employee.objects.create_user(
            email="project@example.com",
            name="Project HR",
            password="pass123",
            role="PROJECT_HR"
        )

        self.other_hr = Employee.objects.create_user(
            email="other@example.com",
            name="Other HR",
            password="pass123",
            role="PROJECT_HR"
        )

        self.employee = Employee.objects.create_user(
            email="emp@example.com",
            name="Normal Employee",
            password="pass123",
            role="EMPLOYEE"
        )

        self.project = Project.objects.create(
            project_name="Test Project",
            project_type="BILLABLE",
            hr=self.project_hr,
            created_by=self.project_hr
        )

            # URLs

        self.project_url = reverse("project-list")
        self.membership_url = reverse("projectmembership-list")

    # ----------------------------------------
    # PROJECT TESTS
    # ----------------------------------------

    def test_project_creation_by_project_hr(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "project_name": "New Project",
            "project_type": "BILLABLE",
            "hr": self.project_hr.id
        }

        response = self.client.post(self.project_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_project_creation_by_employee_should_fail(self):
        self.client.force_authenticate(user=self.employee)

        data = {
            "project_name": "Invalid Project",
            "project_type": "BILLABLE",
            "hr": self.project_hr.id
        }

        response = self.client.post(self.project_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ----------------------------------------
    # MEMBERSHIP TESTS
    # ----------------------------------------

    def test_membership_creation_by_correct_hr(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-25",
            "end_date": None
        }

        response = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_membership_creation_by_wrong_hr_should_fail(self):
        self.client.force_authenticate(user=self.other_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-25",
            "end_date": None
        }

        response = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_membership_creation_by_global_hr(self):
        self.client.force_authenticate(user=self.global_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-25",
            "end_date": None
        }

        response = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_active_membership_should_fail(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-25",
            "end_date": None
        }

        # First create
        self.client.post(self.membership_url, data, format='json')

        # Second create (should fail)
        response = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_should_fail(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-30",
            "end_date": "2026-04-20"
        }

        response = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employee_can_only_view_own_membership(self):
        # Create membership
        ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date="2026-04-25"
        )

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.membership_url)

        self.assertEqual(len(response.data), 1)

    def test_project_hr_sees_only_their_projects(self):
        ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date="2026-04-25"
        )

        self.client.force_authenticate(user=self.project_hr)

        response = self.client.get(self.membership_url)

        self.assertEqual(len(response.data), 1)


    # Unauthenticated Access
    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(self.project_url)
        self.assertIn(response.status_code, [401, 403])

    
    # Employee Updating Project
    def test_employee_should_not_update_project(self):
        self.client.force_authenticate(user=self.employee)

        url = reverse("project-detail", args=[self.project.id])

        data = {
            "project_name": "Hacked Project",
            "project_type": "BILLABLE",
            "hr": self.project_hr.id
        }

        response = self.client.put(url, data, format='json')

        # Ideally should be 403 (but might PASS → means bug exists)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Wrong HR Updating Membership
    def test_wrong_hr_cannot_update_membership(self):
        membership = ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date="2026-04-25"
        )

        self.client.force_authenticate(user=self.other_hr)

        url = reverse("projectmembership-detail", args=[membership.id])

        data = {
            "role": "SUPERVISOR"
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    # GLOBAL_HR Override Update
    def test_global_hr_can_update_membership(self):
        membership = ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date="2026-04-25"
        )

        self.client.force_authenticate(user=self.global_hr)

        url = reverse("projectmembership-detail", args=[membership.id])

        data = {
            "role": "SUPERVISOR"
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    # Close Membership → Create New One
    def test_close_membership_and_create_new_one(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "employee": self.employee.id,
            "project": self.project.id,
            "role": "MEMBER",
            "start_date": "2026-04-25",
            "end_date": None
        }

        # Create first active membership
        response1 = self.client.post(self.membership_url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        membership_id = response1.data["id"]

        # Close it
        url = reverse("projectmembership-detail", args=[membership_id])
        response2 = self.client.patch(url, {"end_date": "2026-05-01"}, format='json')

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Create new membership (should PASS now)
        response3 = self.client.post(self.membership_url, data, format='json')

        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)


    # Invalid HR Assignment in Project
    def test_invalid_hr_assignment_should_fail(self):
        self.client.force_authenticate(user=self.project_hr)

        data = {
            "project_name": "Invalid HR Project",
            "project_type": "BILLABLE",
            "hr": self.employee.id  # NOT a PROJECT_HR
        }

        response = self.client.post(self.project_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    # Empty Membership List
    def test_empty_membership_list(self):
        self.client.force_authenticate(user=self.project_hr)

        response = self.client.get(self.membership_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # DB Constraint Test
    def test_db_constraint_allows_only_one_active_membership(self):
        ProjectMembership.objects.create(
            employee=self.employee,
            project=self.project,
            role="MEMBER",
            start_date="2026-04-25",
            end_date=None
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectMembership.objects.create(
                    employee=self.employee,
                    project=self.project,
                    role="MEMBER",
                    start_date="2026-04-26",
                    end_date=None
                )
        
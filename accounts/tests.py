from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Employee

from django.db import IntegrityError, transaction


# =========================
# AUTH TESTS
# =========================

class AuthTests(APITestCase):

    def setUp(self):
        self.user = Employee.objects.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
            role="EMPLOYEE"
        )

    def test_login_success(self):
        url = reverse("login")

        data = {
            "email": "test@example.com",
            "password": "password123"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_login_invalid(self):
        url = reverse("login")

        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        url = reverse("login")

        data = {
            "email": "test@example.com"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =========================
# EMPLOYEE TESTS
# =========================

class EmployeeTests(APITestCase):

    def setUp(self):
        self.hr = Employee.objects.create_user(
            email="hr@example.com",
            name="HR",
            password="password123",
            role="GLOBAL_HR",
            is_staff=True
        )

        self.emp1 = Employee.objects.create_user(
            email="emp1@example.com",
            name="Emp1",
            password="password123",
            role="EMPLOYEE"
        )

        self.emp2 = Employee.objects.create_user(
            email="emp2@example.com",
            name="Emp2",
            password="password123",
            role="EMPLOYEE"
        )

    # =========================
    # CREATE TESTS
    # =========================

    def test_create_employee_by_hr(self):
        self.client.force_authenticate(user=self.hr)

        url = reverse("employee-list")

        data = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "role": "EMPLOYEE"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_employee_by_non_hr(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-list")

        data = {
            "email": "fail@example.com",
            "name": "Fail User",
            "password": "password123",
            "role": "EMPLOYEE"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================
    # UPDATE TESTS
    # =========================

    def test_employee_update_self(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-detail", args=[self.emp1.id])

        data = {
            "email": "emp1@example.com",
            "name": "Updated Name",
            "password": "password123",
            "role": "EMPLOYEE"
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_update_others(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-detail", args=[self.emp2.id])

        data = {
            "email": "emp2@example.com",
            "name": "Hacked Name",
            "password": "password123",
            "role": "EMPLOYEE"
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================
    # DELETE TESTS
    # =========================

    def test_delete_employee_by_hr(self):
        self.client.force_authenticate(user=self.hr)

        url = reverse("employee-detail", args=[self.emp1.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_employee_by_non_hr(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-detail", args=[self.emp2.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================
    # LIST & RETRIEVE TESTS
    # =========================

    def test_list_employees(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 👇 Updated for pagination
        self.assertTrue(len(response.data['results']) >= 2)

    def test_retrieve_employee(self):
        self.client.force_authenticate(user=self.emp1)

        url = reverse("employee-detail", args=[self.emp1.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "emp1@example.com")

    def test_hr_can_update_any_employee(self):
        self.client.force_authenticate(user=self.hr)

        url = reverse("employee-detail", args=[self.emp1.id])

        data = {
            "email": "emp1@example.com",
            "name": "HR Updated Name",
            "password": "password123",
            "role": "EMPLOYEE"
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "HR Updated Name")
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from common.models import BaseModel  # BaseModel provides 'id', 'created_at', 'updated_at'


class EmployeeManager(BaseUserManager):

    def generate_employee_id(self):
        last = self.model.objects.order_by("id").last()
        if not last:
            return "EMP001"
        # Extract numeric part and increment
        last_num = int(last.employee_id.replace("EMP", ""))
        return f"EMP{last_num + 1:03d}"

    def create_user(self, email, name, employee_id=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        
        email = self.normalize_email(email)

        if not employee_id:
            employee_id = self.generate_employee_id()

        user = self.model(
            email=email,
            name=name,
            employee_id=employee_id,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, employee_id=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "GLOBAL_HR")

        return self.create_user(email, name, employee_id, password, **extra_fields)


class Employee(AbstractBaseUser, PermissionsMixin, BaseModel):

    ROLE_CHOICES = [
        ("GLOBAL_HR", "Global HR"),
        ("PROJECT_HR", "Project HR"),
        ("SUPERVISOR", "Supervisor"),
        ("EMPLOYEE", "Employee"),
    ]

    employee_id = models.CharField(max_length=20, unique=True, blank=True)  # Business ID

    email = models.EmailField(unique=True)  # Login

    name = models.CharField(max_length=150)

    designation = models.CharField(max_length=100, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    date_of_joining = models.DateField(auto_now_add=True)  # Auto-filled

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_employees"
    )

    objects = EmployeeManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]  # 'employee_id' is auto-generated, so not required here

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = Employee.objects.generate_employee_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.name}"
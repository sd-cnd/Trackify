from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):

    model = Employee

    list_display = ("id", "employee_id", "email", "name", "role", "is_staff")

    search_fields = ("email", "name", "employee_id")

    ordering = ("email",)

    # 🔥 Important fields
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "designation", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
        ("Other", {"fields": ("employee_id", "created_by")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "password1", "password2", "role"),
        }),
    )
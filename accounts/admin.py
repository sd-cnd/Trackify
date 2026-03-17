# accounts/admin.py
from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "email", "role", "date_of_joining")
    search_fields = ("employee_id", "name", "email")
from django.contrib import admin
from django.core.exceptions import ValidationError

from attendance.utils import can_mark_attendance
from .models import Attendance
from projects.models import ProjectMembership, Project


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'project',
        'date',
        'status',
        'check_in_time',
        'check_out_time'
    )

    list_filter = ('status', 'date', 'project')

    search_fields = (
        'employee__name',
        'employee__email',
        'project__project_name'
    )

    autocomplete_fields = ['employee', 'project']

    # ✅ FILTER PROJECT AUTOCOMPLETE BASED ON EMPLOYEE
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # 👇 Only apply for project field
        if request.GET.get("field_name") == "project":

            employee_id = request.GET.get("employee")

            if employee_id:
                project_ids = ProjectMembership.objects.filter(
                    employee_id=employee_id
                ).values_list("project_id", flat=True)

                queryset = queryset.filter(id__in=project_ids)

        return queryset, use_distinct

    # ✅ HOLIDAY + LEAVE VALIDATION
    def save_model(self, request, obj, form, change):
        allowed, message = can_mark_attendance(obj.employee, obj.date)

        if not allowed:
            raise ValidationError(message)

        super().save_model(request, obj, form, change)
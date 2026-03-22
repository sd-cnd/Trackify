from django.contrib import admin
from .models import Attendance


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
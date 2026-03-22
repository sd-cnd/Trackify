from django.contrib import admin
from .models import Leave, LeaveQuota


@admin.register(LeaveQuota)
class LeaveQuotaAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'year',
        'el_quota',
        'cl_quota',
        'sl_quota',
        'ol_quota',
        'el_taken',
        'cl_taken',
        'sl_taken',
        'ol_taken'
    )

    list_filter = ('year',)

    search_fields = (
        'employee__name',
        'employee__email'
    )

    autocomplete_fields = ['employee']


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'leave_type',
        'start_date',
        'end_date',
        'status',
        'approved_by'
    )

    list_filter = (
        'leave_type',
        'status',
        'start_date'
    )

    search_fields = (
        'employee__name',
        'employee__email'
    )

    autocomplete_fields = ['employee', 'approved_by']
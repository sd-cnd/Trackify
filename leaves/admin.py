from django.contrib import admin
from .models import Leave, LeaveQuota


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "end_date",
        "status",
        "approved_by"
    )

    list_filter = ("status", "leave_type")

    search_fields = ("employee__name",)

    autocomplete_fields = ("employee", "approved_by")

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(LeaveQuota)
class LeaveQuotaAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "year",
        "el_quota",
        "cl_quota",
        "sl_quota",
        "ol_quota",
        "el_taken",
        "cl_taken",
        "sl_taken",
        "ol_taken",
    )

    search_fields = ("employee__name",)

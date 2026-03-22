from django import forms
from django.contrib import admin
from .models import Project, ProjectMembership
from accounts.models import Employee
from django.core.exceptions import ValidationError


# -------------------------
# Project Admin Form
# -------------------------
class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only PROJECT_HR employees for HR field
        self.fields['hr'].queryset = Employee.objects.filter(role="PROJECT_HR")
        # Only PROJECT_HR employees for created_by field
        self.fields['created_by'].queryset = Employee.objects.filter(role="PROJECT_HR")

    def clean_created_by(self):
        created_by = self.cleaned_data.get('created_by')
        if created_by.role != "PROJECT_HR":
            raise ValidationError("Only PROJECT_HR can be set as created_by")
        return created_by

    def clean_hr(self):
        hr = self.cleaned_data.get('hr')
        if hr.role != "PROJECT_HR":
            raise ValidationError("HR must be a PROJECT_HR employee")
        return hr


# -------------------------
# Project Admin
# -------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = (
        "id",
        "project_name",
        "project_type",
        "supervisor",
        "hr",
        "is_active",
        "created_by",
        "created_at",
    )
    list_filter = ("project_type", "is_active")
    search_fields = ("project_name",)

    def has_delete_permission(self, request, obj=None):
        # Only PROJECT_HR or superuser can delete projects
        return request.user.is_superuser or request.user.role == "PROJECT_HR"

    def has_add_permission(self, request):
        # Only PROJECT_HR or superuser can add projects
        return request.user.is_superuser or request.user.role == "PROJECT_HR"


# -------------------------
# ProjectMembership Admin
# -------------------------
@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("employee", "project", "role", "start_date", "end_date", "is_active")
    list_filter = ("role", "project")
    search_fields = ("employee__name", "project__project_name")

    def is_active(self, obj):
        return obj.end_date is None

    is_active.boolean = True

    def get_queryset(self, request):
        """
        Controls what data is visible in Django Admin
        based on user role.
        """

        qs = super().get_queryset(request)

        # Superuser sees everything
        if request.user.is_superuser:
            return qs

        # GLOBAL_HR sees everything
        if request.user.role == "GLOBAL_HR":
            return qs

        # PROJECT_HR sees only memberships of their projects
        if request.user.role == "PROJECT_HR":
            return qs.filter(project__hr=request.user)

        # Normal employee sees only their own data
        return qs.filter(employee=request.user)
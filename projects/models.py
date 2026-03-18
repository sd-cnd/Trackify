from django.db import models
from common.models import BaseModel
from accounts.models import Employee


class Project(BaseModel):

    PROJECT_TYPE = [
        ("BILLABLE", "Billable"),
        ("NON_BILLABLE", "Non Billable"),
    ]

    project_name = models.CharField(max_length=200)

    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE)

    supervisor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="supervised_projects"
    )

    hr = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hr_projects"
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects"
    )

    def __str__(self):
        return self.project_name


class ProjectMembership(BaseModel):

    ROLE_CHOICES = [
        ("MEMBER", "Member"),
        ("SUPERVISOR", "Supervisor"),
        ("HR", "HR"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    start_date = models.DateField()

    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} -> {self.project.project_name}"
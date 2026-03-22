from django.db import models
from common.models import BaseModel
from accounts.models import Employee
from projects.models import Project


class Attendance(BaseModel):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LEAVE", "Leave"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ("employee", "date")

    def __str__(self):
        return f"{self.employee.name} - {self.date}"
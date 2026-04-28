from django.db import models
from common.models import BaseModel
from accounts.models import Employee
from projects.models import Project

from django.core.exceptions import ValidationError
from .utils import can_mark_attendance
from datetime import date as dt_date


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

    def clean(self):
        allowed, message = can_mark_attendance(self.employee, self.date)

        if not allowed:
            raise ValidationError(message)

        # ✅ Future date validation
        if self.date > dt_date.today():
            raise ValidationError("Cannot mark attendance for future date.")

        # ✅ Time validation
        if self.check_in_time and self.check_out_time:
            if self.check_out_time <= self.check_in_time:
                raise ValidationError("Check-out must be after check-in.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
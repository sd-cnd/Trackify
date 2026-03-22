from django.db import models
from common.models import BaseModel
from accounts.models import Employee


class LeaveQuota(BaseModel):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_quotas"
    )

    year = models.IntegerField()

    el_quota = models.IntegerField(default=12)
    cl_quota = models.IntegerField(default=10)
    sl_quota = models.IntegerField(default=8)
    ol_quota = models.IntegerField(default=2)

    el_taken = models.IntegerField(default=0)
    cl_taken = models.IntegerField(default=0)
    sl_taken = models.IntegerField(default=0)
    ol_taken = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.employee.name} - {self.year}"
    
class Leave(BaseModel):

    LEAVE_TYPES = [
        ("EL", "Earned Leave"),
        ("CL", "Casual Leave"),
        ("SL", "Sick Leave"),
        ("OL", "Optional Leave"),
    ]

    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leaves"
    )

    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="APPLIED"
    )

    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves"
    )

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type}"
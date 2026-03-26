from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta

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

    class Meta:
        unique_together = ("employee", "year")

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

    # -----------------------------
    # VALIDATIONS
    # -----------------------------
    def clean(self):

        # 1. Date validation
        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date")

        # 2. Overlapping leave check
        overlapping = Leave.objects.filter(
            employee=self.employee,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("Overlapping leave already exists")

        # 3. Quota validation
        duration = self.get_duration()

        quota = LeaveQuota.objects.filter(
            employee=self.employee,
            year=self.start_date.year
        ).first()

        if not quota:
            raise ValidationError("Leave quota not defined for this year")

        available = self.get_available_quota(quota)

        # Only validate quota if trying to approve OR already approved
        if self.status == "APPROVED":
            if duration > available:
                raise ValidationError(
                    f"Not enough {self.leave_type} quota. Available: {available}, Required: {duration}"
                )

    # -----------------------------
    # CORE LOGIC METHODS
    # -----------------------------
    def get_duration(self):
        return (self.end_date - self.start_date).days + 1

    def get_available_quota(self, quota):
        mapping = {
            "EL": quota.el_quota - quota.el_taken,
            "CL": quota.cl_quota - quota.cl_taken,
            "SL": quota.sl_quota - quota.sl_taken,
            "OL": quota.ol_quota - quota.ol_taken,
        }
        return mapping[self.leave_type]

    # -----------------------------
    # SAVE OVERRIDE (STATE MGMT)
    # -----------------------------
    def save(self, *args, **kwargs):

        self.full_clean()  # ensure validation always runs

        is_new = self.pk is None

        old_status = None
        if not is_new:
            old_status = Leave.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        # Apply quota when newly approved
        if self.status == "APPROVED" and old_status != "APPROVED":
            self.apply_quota()

        # Revert quota if approval removed
        if old_status == "APPROVED" and self.status != "APPROVED":
            self.revert_quota()

    # -----------------------------
    # QUOTA MANAGEMENT
    # -----------------------------
    def apply_quota(self):
        quota = LeaveQuota.objects.get(
            employee=self.employee,
            year=self.start_date.year
        )

        days = self.get_duration()

        if self.leave_type == "EL":
            quota.el_taken += days
        elif self.leave_type == "CL":
            quota.cl_taken += days
        elif self.leave_type == "SL":
            quota.sl_taken += days
        elif self.leave_type == "OL":
            quota.ol_taken += days

        quota.save()

    def revert_quota(self):
        quota = LeaveQuota.objects.get(
            employee=self.employee,
            year=self.start_date.year
        )

        days = self.get_duration()

        if self.leave_type == "EL":
            quota.el_taken -= days
        elif self.leave_type == "CL":
            quota.cl_taken -= days
        elif self.leave_type == "SL":
            quota.sl_taken -= days
        elif self.leave_type == "OL":
            quota.ol_taken -= days

        quota.save()


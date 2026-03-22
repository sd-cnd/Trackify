from django.db import models
from common.models import BaseModel
from accounts.models import Employee


class Holiday(BaseModel):

    TYPE_CHOICES = [
        ("NATIONAL", "National"),
        ("REGIONAL", "Regional"),
        ("WEEKEND", "Weekend"),
        ("FLEXI", "Flexible"),
    ]

    date = models.DateField()

    name = models.CharField(max_length=200)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    region = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.name} - {self.date}"
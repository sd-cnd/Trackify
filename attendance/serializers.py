from rest_framework import serializers
from django.db import IntegrityError

from .models import Attendance
from .utils import can_mark_attendance


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = "__all__"

    def validate(self, data):
        employee = data.get("employee")
        attendance_date = data.get("date")

        allowed, message = can_mark_attendance(employee, attendance_date)

        if not allowed:
            raise serializers.ValidationError(message)

        return data

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "Attendance already marked for this date."
            )
from rest_framework import serializers
from .models import Project, ProjectMembership
from accounts.models import Employee

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["created_by"]

    def validate_hr(self, value):
        if value.role != "PROJECT_HR":
            raise serializers.ValidationError("Assigned HR must have role PROJECT_HR.")
        return value

    def validate_created_by(self, value):
        if value.role != "PROJECT_HR":
            raise serializers.ValidationError("Created by must be a PROJECT_HR employee.")
        return value


class ProjectMembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectMembership
        fields = "__all__"

    def validate(self, data):
        employee = data.get("employee")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and start_date > end_date:
            raise serializers.ValidationError(
                "End date must be after start date."
            )

        # If membership is active (end_date is null)
        if end_date is None:
            active_membership = ProjectMembership.objects.filter(
                employee=employee,
                end_date__isnull=True
            )
            # Ignore self during update
            if self.instance:
                active_membership = active_membership.exclude(id=self.instance.id)

            if active_membership.exists():
                raise serializers.ValidationError(
                    "Employee already has an active project membership."
                )

        return data
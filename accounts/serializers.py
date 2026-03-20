from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "email",
            "name",
            "designation",
            "role",
            "password",
            "date_of_joining",
            "created_by"
        ]

        read_only_fields = [
            "employee_id",
            "date_of_joining",
            "created_by"
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = Employee.objects.create_user(
            password=password,
            **validated_data
        )

        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
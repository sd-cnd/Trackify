from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Employee
from .serializers import EmployeeSerializer
from .permissions import IsGlobalHR


class EmployeeViewSet(ModelViewSet):

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):

        if self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated, IsGlobalHR]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
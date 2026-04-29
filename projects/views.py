from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from .permissions import IsProjectHR, IsProjectHRForMembership


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    # 👇 Add these
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project_type', 'hr']
    search_fields = ['project_name']
    ordering_fields = ['project_name']
    ordering = ['project_name']

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticated()]
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsProjectHR()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectMembershipViewSet(ModelViewSet):
    queryset = ProjectMembership.objects.select_related("employee", "project")
    serializer_class = ProjectMembershipSerializer

    # 👇 Add these
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'role', 'end_date']
    search_fields = ['employee__name', 'project__project_name']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['start_date']

    def get_permissions(self):
        return [IsAuthenticated(), IsProjectHRForMembership()]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return self.queryset
        if user.role == "GLOBAL_HR":
            return self.queryset
        if user.role == "PROJECT_HR":
            return self.queryset.filter(project__hr=user)
        return self.queryset.filter(employee=user)

    def perform_create(self, serializer):
        project = serializer.validated_data.get("project")
        user = self.request.user

        if user.role == "GLOBAL_HR":
            serializer.save()
            return

        if project.hr != user:
            raise PermissionDenied("You can only assign employees to your own projects.")

        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        if user.role == "GLOBAL_HR":
            serializer.save()
            return

        if instance.project.hr != user:
            raise PermissionDenied("You can only update memberships of your own projects.")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role == "GLOBAL_HR":
            instance.delete()
            return

        if instance.project.hr != user:
            raise PermissionDenied("You can only delete memberships of your own projects.")

        instance.delete()
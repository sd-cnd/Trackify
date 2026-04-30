from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import filters
from rest_framework.decorators import action

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django_filters.rest_framework import DjangoFilterBackend

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from .permissions import IsProjectHR, IsProjectHRForMembership


class ProjectViewSet(ModelViewSet):
    """
    Handles CRUD operations for Projects.
    GET /projects/ - List all projects (authenticated users)
    POST /projects/ - Create a project (PROJECT_HR only)
    GET /projects/{id}/ - Retrieve a project (authenticated users)
    PUT/PATCH /projects/{id}/ - Update a project (PROJECT_HR only)
    DELETE /projects/{id}/ - Delete a project (PROJECT_HR only)
    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

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

    @swagger_auto_schema(
        operation_summary="Delete Project",
        operation_description="Delete a project. Only PROJECT_HR can delete projects.",
        responses={
            204: openapi.Response(description="Project deleted successfully."),
            401: openapi.Response(description="Unauthorized. Authentication credentials were not provided."),
            403: openapi.Response(description="Forbidden. Only PROJECT_HR can delete projects."),
            404: openapi.Response(description="Not Found. Project does not exist."),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProjectMembershipViewSet(ModelViewSet):
    """
    Handles employee-project assignments.
    GET /memberships/ - List memberships (role-based visibility)
    POST /memberships/ - Assign employee to project (PROJECT_HR of that project or GLOBAL_HR)
    GET /memberships/{id}/ - Retrieve a membership
    PUT/PATCH /memberships/{id}/ - Update a membership (PROJECT_HR of that project or GLOBAL_HR)
    DELETE /memberships/{id}/ - Delete a membership (PROJECT_HR of that project or GLOBAL_HR)
    """

    queryset = ProjectMembership.objects.select_related("employee", "project")
    serializer_class = ProjectMembershipSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'role', 'end_date']
    search_fields = ['employee__name', 'project__project_name']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['start_date']

    def get_permissions(self):
        return [IsAuthenticated(), IsProjectHRForMembership()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProjectMembership.objects.none()

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
            raise PermissionDenied(
                "You can only assign employees to your own projects."
            )

        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        if user.role == "GLOBAL_HR":
            serializer.save()
            return

        if instance.project.hr != user:
            raise PermissionDenied(
                "You can only update memberships of your own projects."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role == "GLOBAL_HR":
            instance.delete()
            return

        if instance.project.hr != user:
            raise PermissionDenied(
                "You can only delete memberships of your own projects."
            )

        instance.delete()
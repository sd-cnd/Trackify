from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from .permissions import IsProjectHR, IsProjectHRForMembership



class ProjectViewSet(ModelViewSet):
    """
    Handles CRUD operations for Projects.
    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticated()]

        # Only PROJECT_HR can modify (create/update/delete)
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsProjectHR()]

        # Read allowed for all authenticated users
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Automatically assign 'created_by' as logged-in user.
        """
        serializer.save(created_by=self.request.user)


# --------------------------------------------------


class ProjectMembershipViewSet(ModelViewSet):
    """
    Handles employee-project assignment.

    Includes:
    - Allocation
    - Role assignment
    - History tracking
    """

    # 🚀 Optimization: reduces DB queries
    queryset = ProjectMembership.objects.select_related("employee", "project")

    serializer_class = ProjectMembershipSerializer

    def get_permissions(self):
        """
        Apply custom permission logic for memberships.
        """
        return [IsAuthenticated(), IsProjectHRForMembership()]

    def get_queryset(self):
        """
        Restrict data visibility in API based on role.
        (Same logic as admin, but for API)
        """

        user = self.request.user

        # Superuser → all data
        if user.is_superuser:
            return self.queryset

        # GLOBAL_HR → all data
        if user.role == "GLOBAL_HR":
            return self.queryset

        # PROJECT_HR → only their projects
        if user.role == "PROJECT_HR":
            return self.queryset.filter(project__hr=user)

        # EMPLOYEE → only their own records
        return self.queryset.filter(employee=user)
    
     # 🔥 IMPORTANT: Handle CREATE logic (ownership check)
    def perform_create(self, serializer):
        """
        Enforce that only the HR assigned to a project
        can create memberships for that project.

        GLOBAL_HR can override.
        """

        project = serializer.validated_data.get("project")
        user = self.request.user

        # GLOBAL_HR → full override
        if user.role == "GLOBAL_HR":
            serializer.save()
            return

        # PROJECT_HR must be the assigned HR of the project
        if project.hr != user:
            raise PermissionDenied(
                "You can only assign employees to your own projects."
            )

        serializer.save()

    # 🔥 IMPORTANT: Handle UPDATE/DELETE (object-level control)
    def perform_update(self, serializer):
        """
        Ensure only authorized users can update memberships.
        """

        instance = self.get_object()
        user = self.request.user

        # GLOBAL_HR → override
        if user.role == "GLOBAL_HR":
            serializer.save()
            return

        # PROJECT_HR must match project HR
        if instance.project.hr != user:
            raise PermissionDenied(
                "You can only update memberships of your own projects."
            )

        serializer.save()

    def perform_destroy(self, instance):
        """
        Ensure only authorized users can delete memberships.
        """

        user = self.request.user

        # GLOBAL_HR → override
        if user.role == "GLOBAL_HR":
            instance.delete()
            return

        # PROJECT_HR must match project HR
        if instance.project.hr != user:
            raise PermissionDenied(
                "You can only delete memberships of your own projects."
            )

        instance.delete()
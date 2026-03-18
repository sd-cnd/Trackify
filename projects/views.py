from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from .permissions import IsProjectHR


class ProjectViewSet(ModelViewSet):

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):

        if self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated, IsProjectHR]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectMembershipViewSet(ModelViewSet):

    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipSerializer
    permission_classes = [IsAuthenticated]
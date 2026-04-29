from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectMembershipViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("memberships", ProjectMembershipViewSet, basename="projectmembership")

urlpatterns = [
    path("", include(router.urls)),
]
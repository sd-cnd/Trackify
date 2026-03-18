from rest_framework.routers import DefaultRouter
from .views import ProjectMembershipViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet)
router.register("memberships", ProjectMembershipViewSet)

urlpatterns = router.urls
from django.urls import path, include

from django.urls import include

from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, login_view, logout_view


router = DefaultRouter()
router.register("employees", EmployeeViewSet)

urlpatterns = [
    # Employee APIs
    path("", include(router.urls)),

    # Auth APIs
    path("login/", login_view),
    path("logout/", logout_view),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, login_view, logout_view

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
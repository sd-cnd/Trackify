from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers, filters
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Employee
from .serializers import EmployeeSerializer
from .permissions import IsGlobalHR


# =========================
# Swagger Serializers
# =========================

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_id = serializers.IntegerField()
    employee_id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    role = serializers.CharField()


# =========================
# Employee ViewSet
# =========================

class EmployeeViewSet(ModelViewSet):

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    # 👇 Filtering, searching, ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'designation']
    search_fields = ['name', 'email', 'employee_id']
    ordering_fields = ['name', 'date_of_joining']
    ordering = ['date_of_joining']

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated, IsGlobalHR]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if user.role != "GLOBAL_HR" and instance != user:
            raise PermissionDenied("You cannot update other employees")

        serializer.save(created_by=instance.created_by)


# =========================
# Authentication APIs
# =========================

@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: "Email and password required",
        401: "Invalid credentials"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    login(request, user)

    return Response({
        "message": "Login successful",
        "user_id": user.id,
        "employee_id": user.employee_id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    })


@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response("Logged out successfully"),
        401: "Unauthorized"
    }
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})
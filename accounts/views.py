from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers, filters
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt

from rest_framework_simplejwt.tokens import RefreshToken

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
    access = serializers.CharField()
    refresh = serializers.CharField()
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
    operation_summary="Login",
    operation_description="Authenticate with email and password to receive JWT access and refresh tokens.",
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            description="Login successful. Returns JWT access and refresh tokens along with user details.",
            schema=LoginResponseSerializer
        ),
        400: openapi.Response(description="Bad Request. Email and password are required."),
        401: openapi.Response(description="Unauthorized. Invalid email or password."),
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

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    return Response({
        "access": access,
        "refresh": str(refresh),
        "user_id": user.id,
        "employee_id": user.employee_id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    })


@swagger_auto_schema(
    method='post',
    operation_summary="Logout",
    operation_description="Logout the currently authenticated user by blacklisting their refresh token.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Refresh token to blacklist'
            )
        }
    ),
    responses={
        200: openapi.Response(description="Logout successful."),
        401: openapi.Response(description="Unauthorized. User is not authenticated."),
    }
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass

    return Response({"message": "Logged out successfully"})
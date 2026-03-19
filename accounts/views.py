from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Employee
from .serializers import EmployeeSerializer
from .permissions import IsGlobalHR
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes

# =========================
# Employee ViewSet
# =========================

class EmployeeViewSet(ModelViewSet):

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):

        if self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated, IsGlobalHR]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

# =========================
# Authentication APIs
# =========================

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

@api_view(["POST"])
@authentication_classes([])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})
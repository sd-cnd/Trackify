from rest_framework.permissions import BasePermission

class IsProjectHR(BasePermission):
    """
    Allows only Project HR users to create or delete projects.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Safe methods allowed for all
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Create/Delete allowed only for PROJECT_HR
        if request.method in ["POST", "DELETE"]:
            return request.user.role == "PROJECT_HR"

        return True
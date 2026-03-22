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
    
class IsProjectHRForMembership(BasePermission):
    """
    Only the HR assigned to the project can modify memberships.
    GLOBAL_HR can override everything.
    """

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow read for all
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Allow only HR roles to proceed to object-level check
        return request.user.role in ["PROJECT_HR", "GLOBAL_HR"]

    def has_object_permission(self, request, view, obj):
        """
        Object-level check:
        - GLOBAL_HR → full access
        - PROJECT_HR → only if they are HR of that project
        """

        # GLOBAL_HR override
        if request.user.role == "GLOBAL_HR":
            return True

        # PROJECT_HR must match project.hr
        return obj.project.hr == request.user
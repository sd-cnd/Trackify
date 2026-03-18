from rest_framework.permissions import BasePermission


class IsGlobalHR(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "GLOBAL_HR"
        )
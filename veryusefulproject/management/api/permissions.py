from rest_framework.permissions import BasePermission


class IsAuthenticatedWithJWT(BasePermission):
    def has_permission(self, request, view):
        return True


class IsAuthenticatedWithJWTAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.role_set.filter(name="Admin").exists():
            return False

        return True

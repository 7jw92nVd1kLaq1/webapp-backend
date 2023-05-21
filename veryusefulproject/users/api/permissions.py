from django.conf import settings

from rest_framework.permissions import BasePermission

from .utils import get_user_from_token


class IsAuthenticatedWithJWT(BasePermission):
    def has_permission(self, request, view):
        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        try:
            get_user_from_token(refresh_token_string)
            return True
        except:
            return False


class IsAuthenticatedWithJWTAdmin(BasePermission):
    def has_permission(self, request, view):
        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        try:
            user = get_user_from_token(refresh_token_string)
        except:
            return False

        if not user.role_set.filter(name="Admin").exists():
            return False

        return True

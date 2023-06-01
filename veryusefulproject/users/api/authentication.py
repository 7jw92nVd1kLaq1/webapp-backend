from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken


class JWTAuthentication(BaseJWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        return result

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[settings.SIMPLE_JWT["USER_ID_CLAIM"]]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{settings.SIMPLE_JWT["USER_ID_FIELD"]: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if user.role_set.filter(name=settings.USER_SUSPENDED_ROLE_NAME).exists():
            raise AuthenticationFailed(_("User is suspended"), code="user_suspended")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user

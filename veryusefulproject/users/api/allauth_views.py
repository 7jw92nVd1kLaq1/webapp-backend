from django.contrib.auth import get_user_model
from django.conf import settings

from allauth.socialaccount.helpers import complete_social_login, render_authentication_error
from allauth.socialaccount.providers.oauth2.views import OAuth2View
from allauth.socialaccount.providers.base.constants import AuthError
from allauth.socialaccount.models import SocialLogin

from allauth.utils import get_request_param

from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAuthenticatedWithJWT, IsAuthenticatedWithJWTAdmin
from .serializers import UserSerializer
from .utils import get_tokens_for_user, get_subscription_token_for_user, set_tokens_in_cookie

from datetime import timedelta


User = get_user_model()


class UserViewSet(CreateModelMixin, RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action == 'list':
            permission_classes = [IsAuthenticatedWithJWTAdmin]
        else:
            permission_classes = [IsAuthenticatedWithJWT]

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = get_tokens_for_user(user, subscription=False)

        response = Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return set_tokens_in_cookie(data, response)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

# JWT-Tokens-Related Views


class CheckJWTRefreshTokenValidityView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def get(self, request):
        response = Response()
        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token isn't set in Cookies."}
            return response

        try:
            RefreshToken(token=refresh_token_string)
            response.status_code = status.HTTP_200_OK
            return response
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token is invalid."}
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response


class OAuth2CallbackView(OAuth2View):
    def dispatch(self, request, *args, **kwargs):
        if "error" in request.GET or "code" not in request.GET:
            # Distinguish cancel from error
            auth_error = request.GET.get("error", None)
            if auth_error == self.adapter.login_cancelled_error:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            return render_authentication_error(
                request, self.adapter.provider_id, error=error
            )
        app = self.adapter.get_provider().get_app(self.request)
        client = self.get_client(self.request, app)

        try:
            access_token = self.adapter.get_access_token_data(request, app, client)
            token = self.adapter.parse_token(access_token)
            token.app = app
            login = self.adapter.complete_login(
                request, app, token, response=access_token
            )
            login.token = token
            if self.adapter.supports_state:
                login.state = SocialLogin.verify_and_unstash_state(
                    request, get_request_param(request, "state")
                )
            else:
                login.state = SocialLogin.unstash_state(request)

            # fix this tomorrow
            return complete_social_login(request, login)
        except:
            pass

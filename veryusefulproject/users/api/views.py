from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from defender.utils import add_login_attempt_to_db, check_request, is_already_locked
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


class DeleteJWTTokensView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def get(self, request):
        response = Response()
        try:
            response.delete_cookie("access_token", samesite="None")
            response.delete_cookie("refresh_token", samesite="None")
            response.status_code = status.HTTP_200_OK
        except:
            response.data = {"reason": "Tokens have been unsuccessfully deleted from Cookies."}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        return response


class RenewJWTAccessTokenView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def get(self, request):
        response = Response()
        data = {}
        refresh_token_object = None

        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token isn't set in Cookies."}
            return response

        try:
            refresh_token_object = RefreshToken(token=refresh_token_string)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token is invalid."}
            return response

        data['token'] = str(refresh_token_object.access_token)
        data['username'] = refresh_token_object.get("sub", "No Username")

        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=data["token"],
            max_age=600,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        )
        response.data = {"data": data}

        return response


class RenewJWTSubscriptionTokenView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def get(self, request):
        response = Response()
        data = {}

        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token isn't set in Cookies."}
            return response

        try:
            RefreshToken(token=refresh_token_string)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Refresh token is invalid."}
            return response

        subscription = get_subscription_token_for_user(request.user)
        subscription.set_exp(lifetime=timedelta(minutes=10))

        data['token'] = str(subscription)

        response.set_cookie(
            key='subscription_token',
            value=data["token"],
            expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        )
        response.data = {"data": data}

        return response


class RequestJWTTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        response = Response()
        data = request.data
        user = authenticate(
            request,
            username=data['username'],
            password=data['password']
        )

        if is_already_locked(request, username=data['username']):
            add_login_attempt_to_db(request, False, username=data['username'])
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {
                "reason": "Access Denied. You have run out of attempts to login."}
            return response

        if not user:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"reason": "Access Denied. You have provided the wrong username or password."}
            add_login_attempt_to_db(request, False, username=data['username'])
            check_request(request, True, username=data['username'])
            return response

        add_login_attempt_to_db(request, True, username=data['username'])
        check_request(request, False, username=data['username'])

        data = get_tokens_for_user(user, subscription=False)

        response = set_tokens_in_cookie(data, response)
        response.data = {"data": data}
        return response
##

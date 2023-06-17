from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.generics import CreateAPIView
from defender.utils import add_login_attempt_to_db, check_request, is_already_locked
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import JWTAuthentication
from .serializers import UserSerializer, UserRegistrationSerializer
from .utils import get_tokens_for_user, get_subscription_token_for_user, get_user_from_token, set_tokens_in_cookie

from datetime import timedelta


User = get_user_model()


class UserViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'username'

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = get_tokens_for_user(user)

        response = Response(status=status.HTTP_201_CREATED, headers=headers)
        response = set_tokens_in_cookie(data, response)
        response.data = {'data': {'username': request.data['username'], 'token': data['access']}}

        return response

# JWT-Tokens-Related Views


class CheckJWTAccessTokenValidityView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_200_OK)


class CheckJWTRefreshTokenValidityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response()
        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Refresh token isn\'t set in Cookies.'}
            return response

        try:
            RefreshToken(token=refresh_token_string)
            response.status_code = status.HTTP_200_OK
            return response
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Refresh token is invalid.'}
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'],
                                   samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
            return response


class DeleteJWTTokensView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response()

        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Refresh token isn\'t set in Cookies.'}
            return response

        try:
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'],
                                   samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
            response.status_code = status.HTTP_200_OK
        except:
            response.data = {'reason': 'Tokens have been unsuccessfully deleted from Cookies.'}
            response.status_code = status.HTTP_400_BAD_REQUEST

        return response


class RenewJWTAccessTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response()
        data = {}
        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {'reason': 'Refresh token isn\'t set in Cookies.'}
            return response

        try:
            refresh_token_object = RefreshToken(token=refresh_token_string)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Refresh token is invalid.'}
            return response

        data['token'] = str(refresh_token_object.access_token)
        data['username'] = refresh_token_object.get('sub', 'No Username')

        response.data = {'data': data}
        return response


class RenewJWTSubscriptionTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response()
        data = {}

        refresh_token_string = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)

        if not refresh_token_string:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {'reason': 'Refresh token isn\'t set in Cookies.'}
            return response

        try:
            RefreshToken(token=refresh_token_string)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Refresh token is invalid.'}
            return response

        if not request.query_params.get("channel", None):
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {'reason': 'Provide the name of the channel you are trying to subscribe to.'}
            return response

        subscription = get_subscription_token_for_user(get_user_from_token(refresh_token_string), request.query_params.get("channel"))
        subscription.set_exp(lifetime=timedelta(minutes=10))

        data['token'] = str(subscription)
        response.data = {'data': data}

        return response


class RequestJWTTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        response = Response()
        data = request.data

        if is_already_locked(request, username=data['username']):
            add_login_attempt_to_db(request, False, username=data['username'])
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {
                'reason': 'Access Denied. You have run out of attempts to login. Please contact admins for removing suspension.'}
            return response

        try:
            user = User.objects.get(username=data['username'])
        except:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {'reason': 'Access Denied. You have provided the wrong username or password.'}
            add_login_attempt_to_db(request, False, username=data['username'])
            check_request(request, True, username=data['username'])
            return response

        if not user.check_password(data['password']):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {'reason': 'Access Denied. You have provided the wrong username or password.'}
            add_login_attempt_to_db(request, False, username=data['username'])
            check_request(request, True, username=data['username'])
            return response

        add_login_attempt_to_db(request, True, username=data['username'])
        check_request(request, False, username=data['username'])
        data = get_tokens_for_user(user)

        response = set_tokens_in_cookie(data, response)
        response.data = {'data': {'username': request.data['username'], 'token': data['access']}}
        return response

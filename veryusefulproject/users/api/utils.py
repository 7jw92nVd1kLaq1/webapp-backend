from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, Token, UntypedToken


def set_tokens_in_cookie(data, response):
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=data["access"],
        expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=False,
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'],
        value=data["refresh"],
        expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    )

    return response


def get_tokens_for_user(user, subscription=True):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    if not subscription:
        return {
            'refresh': str(refresh),
            'access': str(access),
        }

    subscription = get_subscription_token_for_user(user)
    subscription["exp"] = access.get("exp")

    return {
        'refresh': str(refresh),
        'access': str(access),
        'subscription': str(subscription)
    }


def get_subscription_token_for_user(user):
    token = UntypedToken.for_user(user)
    token.token_type = "subscription"
    token["channel"] = "marketplace"

    return token


def get_user_from_token(token, refresh_token=True):
    if refresh_token:
        token_obj = RefreshToken(token=token)
    else:
        token_obj = Token(token=token)

    username = token_obj.payload.get('sub', None)
    if not username:
        raise ValidationError("Username is missing from the decoded token.")

    return get_user_model().objects.get(username=username)

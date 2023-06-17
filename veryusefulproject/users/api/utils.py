from django.contrib.auth import get_user_model
from django.conf import settings

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount import signals
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import _add_social_account, _social_login_redirect
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import AuthProcess
from django.http.response import HttpResponseRedirect
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, Token, UntypedToken


User = get_user_model()


def _complete_social_login(request, sociallogin):
    if sociallogin.is_existing:
        signals.social_account_updated.send(
            sender=SocialLogin, request=request, sociallogin=sociallogin
        )
    else:
        # New account, let's connect
        sociallogin.save(request, connect=True)
        signals.social_account_added.send(
            sender=SocialLogin, request=request, sociallogin=sociallogin
        )

    assert User.objects.filter(username=sociallogin.user.username).exists()

    tokens = get_tokens_for_user(sociallogin.user)
    response = HttpResponseRedirect(settings.FRONTEND_URL)
    response = set_tokens_in_cookie(tokens, response)

    return response


# delete COOKIES if the set cookies are invalid
def _social_login_redirect(request, sociallogin):
    response = HttpResponseRedirect(settings.FRONTEND_URL)
    user_refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'], None)
    if user_refresh_token:
        try:
            user = get_user_from_token(user_refresh_token)
            return response
        except:
            pass

    tokens = get_tokens_for_user(sociallogin.user)
    return set_tokens_in_cookie(tokens, response)


def complete_social_login(request, sociallogin):
    assert not sociallogin.is_existing
    sociallogin.lookup()
    try:
        get_adapter(request).pre_social_login(request, sociallogin)
        signals.pre_social_login.send(
            sender=SocialLogin, request=request, sociallogin=sociallogin
        )
        process = sociallogin.state.get("process")
        if process == AuthProcess.REDIRECT:
            return _social_login_redirect(request, sociallogin)
        elif process == AuthProcess.CONNECT:
            return _add_social_account(request, sociallogin)
        else:
            return _complete_social_login(request, sociallogin)
    except ImmediateHttpResponse as e:
        return e.response


def set_tokens_in_cookie(data, response):
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_REFRESH_COOKIE'],
        value=data["refresh"],
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    )

    return response


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    tokens = {
        'refresh': str(refresh),
        'access': str(access),
    }

    return tokens


def get_subscription_token_for_user(user, channel):
    token = UntypedToken.for_user(user)
    token.token_type = "subscription"
    token["channel"] = channel 

    return token


def get_user_from_token(token, refresh_token=True):
    if refresh_token:
        token_obj = RefreshToken(token=token)
    else:
        token_obj = Token(token=token)

    username = token_obj.payload.get('sub', None)
    if not username:
        raise ValidationError("Username is missing from the decoded token.")

    print("This user is {}".format(username))

    return get_user_model().objects.get(username=username)

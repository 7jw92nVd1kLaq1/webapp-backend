from django.contrib.auth import get_user_model
from django.conf import settings

from django.core.exceptions import PermissionDenied

from requests import RequestException
from time import time

from allauth.utils import get_request_param, generate_unique_username
from allauth.account.utils import setup_user_email
from allauth.socialaccount import app_settings
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.views import OAuth2View
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.base.constants import AuthError
from allauth.socialaccount.models import SocialLogin
from django.http.response import HttpResponseRedirect
from django.utils.crypto import get_random_string

from .utils import complete_social_login

import random


User = get_user_model()


class ModifiedSocialLogin(SocialLogin):
    def save(self, request, connect=False):
        """
        Saves a new account. Note that while the account is new,
        the user may be an existing one (when connecting accounts)
        """
        assert not self.is_existing
        user = self.user
        # Custom Code goes here

        if User.objects.filter(username=user.username).exists():
            while True:
                new_username = get_random_string(length=random.randint(20, 50))
                if not User.objects.filter(username=new_username).exists():
                    break

        user.set_nickname(get_random_string(length=15))
        user.set_unusable_second_password()
        ###
        user.save()
        self.account.user = user
        self.account.save()
        if app_settings.STORE_TOKENS and self.token and self.token.app_id:
            self.token.account = self.account
            self.token.save()
        if connect:
            # TODO: Add any new email addresses automatically?
            pass
        else:
            setup_user_email(request, user, self.email_addresses)


class OAuth2CallbackView(OAuth2View):
    def dispatch(self, request, *args, **kwargs):
        if "error" in request.GET or "code" not in request.GET:
            # Distinguish cancel from error
            auth_error = request.GET.get("error", None)
            if auth_error == self.adapter.login_cancelled_error:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            # Fixed
            return HttpResponseRedirect(settings.FRONTEND_URL)
            ####

        app = self.adapter.get_provider().get_app(self.request)
        client = self.get_client(self.request, app)

        try:
            access_token = self.adapter.get_access_token_data(request, app, client)
            token = self.adapter.parse_token(access_token)
            token.app = app

            # Fixed
            login = self.adapter.complete_login(
                request, app, token, response=access_token
            )
            ####
            login.token = token
            if self.adapter.supports_state:
                login.state = SocialLogin.verify_and_unstash_state(
                    request, get_request_param(request, "state")
                )
            else:
                login.state = SocialLogin.unstash_state(request)

            # Fixed
            return complete_social_login(request, login)
            ####
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
            Exception
        ) as e:
            # Redirect a user to the homepage of the front-end website.
            return HttpResponseRedirect(settings.FRONTEND_URL)

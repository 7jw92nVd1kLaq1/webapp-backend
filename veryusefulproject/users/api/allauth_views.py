from django.contrib.auth import get_user_model
from django.conf import settings

from django.core.exceptions import PermissionDenied

from requests import RequestException

from allauth.socialaccount import app_settings
from allauth.socialaccount.helpers import complete_social_login, render_authentication_error
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.views import OAuth2View
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.base.constants import AuthError
from allauth.socialaccount.models import SocialAccount, SocialLogin, SocialToken
from allauth.utils import get_request_param
from django.http.response import HttpResponseRedirect
from django.utils.crypto import get_random_string

from .utils import complete_social_login


User = get_user_model()


class ModifiedSocialLogin(SocialLogin):
    def save(self, request, connect=False):
        """
        Saves a new account. Note that while the account is new,
        the user may be an existing one (when connecting accounts)
        """
        assert not self.is_existing
        user = self.user
        user.set_nickname(get_random_string(length=15))
        user.set_second_password(get_random_string(length=255))
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

    def lookup(self):
        assert not self.is_existing
        try:
            a = SocialAccount.objects.get(
                provider=self.account.provider, uid=self.account.uid
            )
            # Update account
            a.extra_data = self.account.extra_data
            self.account = a
            self.user = self.account.user
            a.save()
            # Update token
            if app_settings.STORE_TOKENS and self.token and self.token.app.pk:
                assert not self.token.pk
                try:
                    t = SocialToken.objects.get(
                        account=self.account, app=self.token.app
                    )
                    t.token = self.token.token
                    if self.token.token_secret:
                        # only update the refresh token if we got one
                        # many oauth2 providers do not resend the refresh token
                        t.token_secret = self.token.token_secret
                    t.expires_at = self.token.expires_at
                    t.save()
                    self.token = t
                except SocialToken.DoesNotExist:
                    self.token.account = a
                    self.token.save()
            return True
        except SocialAccount.DoesNotExist:
            return False


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
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            print("Failed because one of four reasons")
        except Exception as c:
            print("FAILEDDDD!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(c)

        return HttpResponseRedirect(settings.FRONTEND_URL)

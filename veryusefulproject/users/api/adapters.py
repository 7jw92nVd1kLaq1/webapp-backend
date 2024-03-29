from allauth.socialaccount import app_settings
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.models import SocialAccount

import requests

class CustomGitHubProvider(GitHubProvider):
    def sociallogin_from_response(self, request, response):
        from .allauth_views import ModifiedSocialLogin as SocialLogin
        
        ## Issues to fix: there may exist two different accounts with the same username of the different providers.
        ## To fix this, do the following:
        ## 1. Check the UID of the account - the same UID may be allowed as long as they are of different providers.
        ## 1.1 If the UID already exists, assign JWT tokens to a user and redirect him to the home page of the front-end website
        ## 2. Check the username of the account and search DB to check the existence of a user with the same username.
        ## 3. If exists, generate the arbitrary username of an account and save to DB.
        adapter = get_adapter(request)
        uid = self.extract_uid(response)
        extra_data = self.extract_extra_data(response)
        common_fields = self.extract_common_fields(response)
        socialaccount = SocialAccount(extra_data=extra_data, uid=uid, provider=self.id)
        email_addresses = self.extract_email_addresses(response)
        self.cleanup_email_addresses(common_fields.get("email"), email_addresses)
        sociallogin = SocialLogin(
            account=socialaccount, email_addresses=email_addresses
        )
        user = sociallogin.user = adapter.new_user(request, sociallogin)
        user.set_unusable_password()
        adapter.populate_user(request, sociallogin, common_fields)
        return sociallogin

class CustomGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": "token {}".format(token.token)}
        resp = requests.get(self.profile_url, headers=headers)
        resp.raise_for_status()
        extra_data = resp.json()
        if app_settings.QUERY_EMAIL and not extra_data.get("email"):
            extra_data["email"] = self.get_email(headers)
        return CustomGitHubProvider(request=request).sociallogin_from_response(request, extra_data)

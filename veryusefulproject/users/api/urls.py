from django.urls import path

from allauth.socialaccount.providers.github.provider import GitHubProvider

from veryusefulproject.users.api.allauth_views import OAuth2CallbackView
from .adapters import CustomGitHubOAuth2Adapter

github_login_callback = OAuth2CallbackView.adapter_view(CustomGitHubOAuth2Adapter)

urlpatterns = [
    path(("accounts/" + GitHubProvider.id + "/login/callback_/"), view=github_login_callback, name=GitHubProvider.id + "_callback"),
]

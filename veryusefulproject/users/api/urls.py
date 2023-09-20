from django.urls import path

from .allauth_views import OAuth2CallbackView
from .adapters import CustomGitHubOAuth2Adapter, CustomGitHubProvider as GitHubProvider

github_login_callback = OAuth2CallbackView.adapter_view(CustomGitHubOAuth2Adapter)

urlpatterns = [
    path(("accounts/" + GitHubProvider.id + "/login/callback_/"), view=github_login_callback, name=GitHubProvider.id + "_callback"),
]

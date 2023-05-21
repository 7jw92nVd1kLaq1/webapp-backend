from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from veryusefulproject.core.api.views import CsrfView
from veryusefulproject.users.api.views import UserViewSet, CheckJWTRefreshTokenValidityView, DeleteJWTTokensView, RenewJWTAccessTokenView, RenewJWTSubscriptionTokenView, RequestJWTTokenView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet, basename="user")


app_name = "api"
urlpatterns = router.urls

urlpatterns += (
    path("csrftoken/", CsrfView.as_view(), name="csrftoken"),
)

# JWT-Tokens-Related Views
urlpatterns += (
    path("request-tokens/", RequestJWTTokenView.as_view(), name="request-tokens"),
    path("renew-sub-token/", RenewJWTSubscriptionTokenView.as_view(), name="renew-sub-token"),
    path("renew-acc-token/", RenewJWTAccessTokenView.as_view(), name="renew-acc-token"),
    path("delete-tokens/", DeleteJWTTokensView.as_view(), name="delete-tokens"),
    path("check-ref-token/", CheckJWTRefreshTokenValidityView.as_view(), name="check-ref-token"),
)

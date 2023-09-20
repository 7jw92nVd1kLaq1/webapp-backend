from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from veryusefulproject.core.api.views import CsrfView
from veryusefulproject.management.api.views import AdminUsersViewSet
from veryusefulproject.orders.views import UserOrderListView
from veryusefulproject.orders.api.views import OrderCreationView, RequestItemInfoView, ListUserOrderView, OrderRetrieveView
from veryusefulproject.request_marketplace.api.views import DisplayAvailableOffersView, SignUpOrderIntermediaryApplicantView
from veryusefulproject.users.api.views import CheckJWTAccessTokenValidityView, UserRegistrationView, UserViewSet, CheckJWTRefreshTokenValidityView, DeleteJWTTokensView, RenewJWTAccessTokenView, RenewJWTSubscriptionTokenView, RequestJWTTokenView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet, basename="user")
router.register("admin-user-management", AdminUsersViewSet, basename="admin-user")


app_name = "api"
urlpatterns = router.urls

urlpatterns += (
    path("csrftoken/", CsrfView.as_view(), name="csrftoken"),
)

# JWT-Tokens-Related Views
urlpatterns += (
    path("registration/", UserRegistrationView.as_view(), name="user-registration"),
    path("request-tokens/", RequestJWTTokenView.as_view(), name="request-tokens"),
    path("renew-sub-token/", RenewJWTSubscriptionTokenView.as_view(), name="renew-sub-token"),
    path("renew-acc-token/", RenewJWTAccessTokenView.as_view(), name="renew-acc-token"),
    path("delete-tokens/", DeleteJWTTokensView.as_view(), name="delete-tokens"),
    path("check-ref-token/", CheckJWTRefreshTokenValidityView.as_view(), name="check-ref-token"),
    path("check-acc-token/", CheckJWTAccessTokenValidityView.as_view(), name="check-acc-token"),
)

urlpatterns += (
    path("parseItemURL/", RequestItemInfoView.as_view(), name="parse-item-url"),
    path("create-order/", OrderCreationView.as_view(), name="create-order"),
    path("list-order/", ListUserOrderView.as_view(), name="list-order"),
    path("test-order/", UserOrderListView.as_view(), name="test-order"),
    path("order-detail/<uuid:pk>/", OrderRetrieveView.as_view(), name="order-detail")
)

urlpatterns += (
    path("list-requests/", DisplayAvailableOffersView.as_view(), name="list-requests"),
    path("sign-user-up-order/", SignUpOrderIntermediaryApplicantView.as_view(), name="sign-user-up-order"),
)

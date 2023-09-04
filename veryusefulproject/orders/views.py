from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from veryusefulproject.users.api.authentication import JWTAuthentication
from veryusefulproject.orders.models import Order, OrderItem
from veryusefulproject.orders.api.serializers import OrderSerializer

from django.db.models import Prefetch
from django.contrib.auth import get_user_model
# Create your views here.


User = get_user_model()


class UserOrderListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response()

        if not request.user.is_authenticated:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        orders = Order.objects.select_related("status",
                                              "orderintermediarylink__intermediary").prefetch_related(Prefetch("order_items")).only("status__step", "orderintermediarylink__intermediary__username")

        serializer = OrderSerializer(orders, many=True, fields=["status", "intermediary", "order_items"], context={
                                     "intermediary": {"fields": ["username"]}})

        response.status_code = status.HTTP_200_OK
        response.data = serializer.data
        return response

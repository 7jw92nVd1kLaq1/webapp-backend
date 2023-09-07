from django.db.models import Q, Prefetch, Avg
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.currencies.models import CryptoCurrency
from veryusefulproject.orders.models import Order, OrderItem, OrderReview
from veryusefulproject.orders.api.serializers import OrderSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

from .paginations import RequestsListPagination


class DisplayAvailableOffersView(PaginationHandlerMixin, APIView):
    authentication_classes = [JWTAuthentication]
    pagination_class = RequestsListPagination
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        only_fields = [
            "url_id",
            "created_at",
            "orderaddresslink__address__country",
            "ordercustomerlink__customer__username",
            "ordercustomerlink__customer__date_joined",
            "orderpaymentlink__payment__additional_cost",
            "orderpaymentlink__payment__fiat_currency__symbol",
            "orderpaymentlink__payment__fiat_currency__ticker",
            "orderpaymentlink__payment__order_payment_balance__payment_method__ticker",
        ]

        username = request.user.get_username()

        queryset = Order.objects.select_related(
            "orderaddresslink__address",
            "ordercustomerlink__customer",
            "orderpaymentlink__payment__fiat_currency",
            "orderpaymentlink__payment__order_payment_balance__payment_method",
        ).prefetch_related(
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.all().only("name", "price")
            )
        ).only(*only_fields)
        """
        queryset = Order.objects.select_related(
            "orderaddresslink__address",
            "ordercustomerlink__customer",
            "orderpaymentlink__payment__fiat_currency",
            "orderpaymentlink__payment__order_payment_balance__payment_method",
        ).prefetch_related(
            Prefetch(
                "order_reviews",
                queryset=OrderReview.objects.select_related("user").all().only("rating")
            ),
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.select_related("company").all().only("name", "price")
            )
        ).exclude(
            Q(ordercustomerlink__customer__username=username) |
            Q(orderintermediarylink__intermediary__username__regex=r"^[\w]+")
        ).only(*only_fields)
        """

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page,
                    many=True,
                    fields=["address", "customer", "order_items", "payment", "url_id", "created_at"],
                    context={
                        "user": {"fields": ["username", "date_joined"]},
                        "address": {"fields": ["country"]},
                        "payment": {"fields": ["additional_cost", "fiat_currency", "order_payment_balance"]},
                        "order_items": {"fields": ["name", "price", "image_url", "options", "quantity", "url"]},
                        "order_payment_balance": {"fields": ["payment_method"]},
                    }
                ).data
            )
        else:
            serializer = self.serializer_class(
                queryset,
                many=True,
                fields=["address", "customer", "order_items", "payment", "url_id", "created_at"], 
                context={
                    "user": {"fields": ["username", "date_joined"]},
                    "address": {"fields": ["country"]},
                    "payment": {"fields": ["additional_cost", "fiat_currency", "order_payment_balance"]},
                    "order_items": {"fields": ["name", "price", "image_url", "options", "quantity", "url"]},
                    "order_payment_balance": {"fields": ["payment_method"]},
                }
            )
        
        data = serializer.data
        results = list(data['results'])


        ## Complie a list of average rating of every customer so far since its registration in a page
        user_ratings = {}
        users = set([order["customer"]["customer"]["username"] for order in results if order.get("customer")])
        for user in users:
            user_avg_rating = OrderReview.objects.filter(user__username=user).aggregate(Avg("rating"))["rating__avg"]
            user_ratings[user] = user_avg_rating

        for x in range(len(results)):
            # Assign the rate of Cryptocurrency at the time of the creation of an order
            if results[x].get("payment", None):
                cryptocurrency = CryptoCurrency.objects.get(ticker=results[x]["payment"]["payment"]["order_payment_balance"]["payment_method"]["ticker"])
                cryptocurrency_rate = cryptocurrency.cryptocurrencyrate_set.filter(Q(created_at__lte=results[x]["created_at"])).order_by("created_at").only("rate").last()
                
                data["results"][x]["payment"]["payment"]["order_payment_balance"]["payment_method"]["rate"] = float(cryptocurrency_rate.rate)
            
            # Assign the average rating to every order of a customer
            if data['results'][x]['customer']:
                username = data['results'][x]['customer']['customer']['username'] 
                data['results'][x]['customer']['customer']['average_rating'] = user_ratings[username] 

        return Response(status=status.HTTP_200_OK, data=data)

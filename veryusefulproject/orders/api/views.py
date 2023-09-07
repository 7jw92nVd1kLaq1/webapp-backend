from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from ..paginations import ListOrderPagination
from ..tasks import get_product_info, create_order

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.orders.models import Order, OrderStatus
from veryusefulproject.orders.api.serializers import OrderSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

from django.db.models import Q


class RequestItemInfoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        url = request.data.get("url", None)

        if not url:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "You forgot to provide an URL."})
        """
        if not check_if_valid_url(url):
            print("Not a valid URL")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        """

        get_product_info.delay(url, request.user.get_username())
        return Response(status=status.HTTP_200_OK)


class OrderCreationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please log-in."})

        create_order.delay(request.data, request.user.get_username())
        return Response(status=status.HTTP_200_OK)


class OrderRetrieveView(RetrieveAPIView):
    serializer_class = OrderSerializer

    def return_data_for_deposit_status(self, order_id):
        deferred_fields = [
            "status__name",
            "status__desc",
            "status__created_at",
            "status__modified_at",
            "orderaddresslink__created_at",
            "orderaddresslink__modified_at",
            "orderpaymentlink__created_at",
            "orderpaymentlink__modified_at",
            "orderpaymentlink__payment__fiat_currency",
            "orderpaymentlink__payment__discount",
            "orderpaymentlink__payment__created_at",
            "orderpaymentlink__payment__modified_at",
        ]
        order_qs = Order.objects.prefetch_related("order_items").select_related(
            "orderaddresslink__address", 
            "orderpaymentlink__payment__order_payment_balance__payment_method", 
            "status"
        ).filter(
            url_id=order_id
        ).defer(*deferred_fields)

        if not order_qs.exists():
            return {}

        serializer = self.get_serializer_class()(
            order_qs.first(),
            fields_exclude=[
                "customer",
                "intermediary",
                "orderdispute_set",
                "messages",
                "order_reviews"
            ],
            context={
                "address": {"fields": ["address"]},
                "payment": {"fields_exclude": ["discount", "fiat_currency", "created_at", "modified_at"]},
                "order_items": {"fields_exclude": ["tracking", "order_identifier", "order", "created_at", "modified_at"]},
                "order_payment_balance": {"fields": ["payment_method", "deposit_address", "balance"]},
                "payment_method": {"fields": ["ticker", "name", "cryptocurrencyrate_set"]},
                "cryptocurrencyrate_set": {"created_at": order_qs.first().created_at, "fields": ["rate"]}
            }
        )

        return serializer.data

    def retrieve(self, request, *args, **kwargs):
        order_id = kwargs.get("pk", "")
        if not order_id:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the ID of an order."})

        order_qs = Order.objects.select_related("status").filter(url_id=order_id).only("status__step")
        if not order_qs.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the valid ID of an order."})

        status_id = order_qs.first().status.step

        if status_id == 1:
            data = self.return_data_for_deposit_status(order_id)
            return Response(status=status.HTTP_200_OK, data=data)
        else:
            pass

        return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the ID of an order."})


class ListUserOrderView(PaginationHandlerMixin, APIView):
    pagination_class = ListOrderPagination
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def get_user_all_orders(self):
        user = self.request.user

        orders = Order.objects.select_related(
            "status", 
            "orderintermediarylink__intermediary", 
            "ordercustomerlink__customer"
        ).prefetch_related(
            "order_items"
        ).filter(
            Q(ordercustomerlink__customer__username=user.get_username()) | 
            Q(orderintermediarylink__intermediary__username=user.get_username())
        ).only(
            "status__step", 
            "ordercustomerlink__customer__username", 
            "orderintermediarylink__intermediary__username", 
            "url_id", 
            "created_at"
        )

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=["status", "customer", "intermediary", "order_items", "url_id", "created_at"], 
                    context={
                        "intermediary": {"fields": ["username"]}, 
                        "customer": {"fields": ["username"]}, 
                        "order_items": {"fields": ['name']}
                    }
                ).data
            )

        else:
            serializer = self.serializer_class(
                orders, 
                many=True, 
                fields=["status", "customer", "intermediary", "order_items", "url_id", "created_at"], 
                context={
                    "intermediary": {"fields": ["username"]}, 
                    "customer": {"fields": ["username"]}, 
                    "order_items": {"fields": ["name"]}}
            )

        return serializer.data

    def get_user_customer_orders(self):
        user = self.request.user

        orders = Order.objects.select_related(
            "status", 
            "ordercustomerlink__customer"
        ).prefetch_related(
            "order_items"
        ).filter(
            ordercustomerlink__customer__username=user.get_username()
        ).only(
            "status__step", 
            "ordercustomerlink__customer__username", 
            "url_id", 
            "created_at"
        )

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=["status", "customer", "order_items", "url_id", "created_at"], 
                    context={
                        "customer": {"fields": ["username"]}, 
                        "order_items": {"fields": ["name"]}
                    }
                ).data
            )
        else:
            serializer = self.serializer_class(
                orders, 
                many=True, 
                fields=["status", "customer", "order_items", "url_id", "created_at"], 
                context={
                    "customer": {"fields": ["username"]}, 
                    "order_items": {"fields": ["name"]}
                }
            )

        return serializer.data

    def get_user_intermediary_orders(self):
        user = self.request.user

        orders = Order.objects.select_related(
            "status", 
            "orderintermediarylink__intermediary"
        ).prefetch_related(
            "order_items"
        ).filter(
            orderintermediarylink__intermediary__username=user.get_username()
        ).only(
            "status__step", 
            "orderintermediarylink__intermediary__username", 
            "url_id", 
            "created_at"
        )

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=["status", "intermediary", "order_items", "url_id", "created_at"], 
                    context={
                        "intermediary": {"fields": ["username"]}, 
                        "order_items": {"fields": ['name']}
                    }
                ).data
            )
        else:
            serializer = self.serializer_class(
                orders, 
                many=True, 
                fields=["status", "intermediary", "order_items", "url_id", "created_at"], 
                context={
                    "intermediary": {"fields": ["username"]}, 
                    "order_items": {"fields": ['name']}
                }
            )

        return serializer.data

    def get(self, request):
        data = None
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please log-in."})

        target = request.query_params.get('for', '')

        if not target or target == 'all':
            data = self.get_user_all_orders()
        elif target == 'customer':
            data = self.get_user_customer_orders()
        elif target == 'intermediary':
            data = self.get_user_intermediary_orders()
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "You have supplied the unknown argument for the parameter \"for\"."}
            )

        return Response(status=status.HTTP_200_OK, data=data)

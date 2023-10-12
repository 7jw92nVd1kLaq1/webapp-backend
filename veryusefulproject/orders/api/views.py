from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from ..paginations import ListOrderPagination
from ..tasks import get_product_info, create_order
from ..utils import return_data_for_finding_intermediary, return_data_for_deposit_status

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.orders.models import Order, OrderIntermediaryCandidate, OrderIntermediaryLink, OrderStatus
from veryusefulproject.orders.api.serializers import OrderSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q


User = get_user_model()


class RequestItemInfoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        url = request.data.get("url", None)

        if not url:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "You forgot to provide an URL."})

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        order_id = kwargs.get("pk", None)
        if order_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the ID of an order."})

        order_qs = Order.objects.select_related("status").filter(url_id=order_id).only("status__step")
        if not order_qs.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "There is no order with the provided ID. Please provide the valid ID of an order."})

        status_id = order_qs.first().status.step

        if status_id == 1:
            data = return_data_for_finding_intermediary(order_id)
            if not data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_200_OK, data=data)
        else:
            data = return_data_for_finding_intermediary(order_id)
            if not data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_200_OK, data=data)


class OrderUpdateView(UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def update_order_intermediary(self, order, data):
        """
        This assigns an intermediary to an order, data must be of \"dict\" type and contain the
        \"username\" of an intermediary.
        """
        if not data.get("username", None):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the username of an intermediary you chose."})

        candidate = OrderIntermediaryCandidate.objects.select_related("user").filter(order=order, user__username=data.get("username"))

        if not candidate.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "The username you provided is not a part of candidates of this order."})

        with transaction.atomic():
            try:
                OrderIntermediaryLink.objects.create(order=order, intermediary=candidate.first().user)
            except:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "An error has occurred while assigning a candidate to an intermediary of this order. Please try again."})

            order.status = OrderStatus.objects.get(step=order.status.step+1)
            order.save()

            data = return_data_for_deposit_status(order.url_id)
            return Response(status=status.HTTP_201_CREATED, data=data)


    def update(self, request, *args, **kwargs):
        if request.method != "PATCH":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        data = request.data
        if not data.get("order_id", None):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "Please provide the ID of an order."})

        order_qs = Order.objects.select_related("status").filter(
            ordercustomerlink__customer=self.request.user, 
            url_id=data.get("order_id")
        ).only("url_id", "status__step")

        if not order_qs.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "No order with the given order ID exists."})

        order = order_qs.first()
        order_step = order.status.step
        if order_step == 1:
            return self.update_order_intermediary(order, data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data=return_data_for_finding_intermediary(order.url_id))


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

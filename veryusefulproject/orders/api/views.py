from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from ..paginations import ListOrderPagination
from ..tasks import get_product_info, create_order
from ..utils import return_data_for_finding_intermediary, update_order_additional_info, update_order_intermediary

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.orders.models import Order
from veryusefulproject.orders.api.serializers import OrderSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()


class RequestItemInfoView(APIView):
    """
    This view is used to request information about an item from the given URL. No HTTP 
    method is allowed except POST.
    """

    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        url = request.data.get("url", None)

        if not url:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "You forgot to provide an URL."}
            )

        get_product_info.delay(url, request.user.get_username())
        return Response(status=status.HTTP_200_OK)


class OrderCreationView(APIView):
    """
    This view is used to create an order. It requires the user to be authenticated. No
    HTTP method is allowed except POST.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        if not request.user.is_authenticated:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please log-in."}
            )

        create_order.delay(request.data, request.user.get_username())
        return Response(status=status.HTTP_200_OK)


class OrderRetrieveView(RetrieveAPIView):
    """
    This view is used to retrieve an order. It requires the user to be authenticated. No
    HTTP method is allowed except GET.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        order_id = kwargs.get("pk", None)
        if order_id is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the ID of an order."}
            )

        order_qs = Order.objects.select_related("status").filter(url_id=order_id).only("status__step")
        if not order_qs.exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "There is no order with the provided ID. Please provide the valid ID of an order."}
            )

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
    """
    This view is used to update an order. It requires the user to be authenticated. No
    HTTP method is allowed except PATCH.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def update(self, request, *args, **kwargs):
        """
        This method is used to update an existing order, and fully processes when the 
        view receives a PATCH request.
        """
        if request.method != "PATCH":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        data = request.data
        if not data.get("order_id", None):
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the ID of an order."}
            )

        order_qs = Order.objects.select_related("status").filter(
            ordercustomerlink__customer=self.request.user, 
            url_id=data.get("order_id")
        ).only("url_id", "status__step")

        if not order_qs.exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "No order with the given order ID exists."}
            )

        order = order_qs.first()
        order_step = order.status.step
        if order_step == 1:
            if data.get("for", None) == "update_additional_info":
                return update_order_additional_info(order, data)
            return update_order_intermediary(order, data)

        return Response(
            status=status.HTTP_400_BAD_REQUEST, 
            data=return_data_for_finding_intermediary(order.url_id)
        )


class ListUserOrderView(PaginationHandlerMixin, APIView):
    """
    This view is used to list all orders of the user. It requires the user to be 
    authenticated. No HTTP method is allowed except GET.
    """

    pagination_class = ListOrderPagination
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_user_all_orders(self):
        """
        This method returns all orders of the user.
        """

        user = self.request.user
        
        # The following queryset selects all orders of the user.
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
        
        # It is used to paginate the queryset.
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=[
                        "status", 
                        "customer", 
                        "intermediary", 
                        "order_items", 
                        "url_id", 
                        "created_at"
                    ], 
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
                fields=[
                    "status", 
                    "customer", 
                    "intermediary", 
                    "order_items", 
                    "url_id", 
                    "created_at"
                ], 
                context={
                    "intermediary": {"fields": ["username"]}, 
                    "customer": {"fields": ["username"]}, 
                    "order_items": {"fields": ["name"]}}
            )

        return serializer.data

    def get_user_customer_orders(self):
        """
        This method returns all orders of the user as a customer.
        """

        user = self.request.user
        
        # The following queryset selects all orders of the user as a customer.
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
        
        # It is used to paginate the queryset.
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=[
                        "status", 
                        "customer", 
                        "order_items", 
                        "url_id", 
                        "created_at"
                    ], 
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
                fields=[
                    "status", 
                    "customer", 
                    "order_items", 
                    "url_id", 
                    "created_at"
                ], 
                context={
                    "customer": {"fields": ["username"]}, 
                    "order_items": {"fields": ["name"]}
                }
            )

        return serializer.data

    def get_user_intermediary_orders(self):
        """
        This method returns all orders of the user as an intermediary.
        """

        user = self.request.user
        
        # The following queryset selects all orders of the user as an intermediary.
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
        
        # It is used to paginate the queryset.
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(
                    page, 
                    many=True, 
                    fields=[
                        "status", 
                        "intermediary", 
                        "order_items", 
                        "url_id", 
                        "created_at"
                    ], 
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
                fields=[
                    "status", 
                    "intermediary", 
                    "order_items", 
                    "url_id", 
                    "created_at"
                ], 
                context={
                    "intermediary": {"fields": ["username"]}, 
                    "order_items": {"fields": ['name']}
                }
            )

        return serializer.data

    def get(self, request):
        """
        This method is run when the view receives a GET request.
        """

        data = None
        target = request.query_params.get('for', '')

        if not target or target == 'all':
            data = self.get_user_all_orders()
        elif target == 'customer':
            data = self.get_user_customer_orders()
        elif target == 'intermediary':
            data = self.get_user_intermediary_orders()
        else:
            data = self.get_user_all_orders()

        return Response(status=status.HTTP_200_OK, data=data)

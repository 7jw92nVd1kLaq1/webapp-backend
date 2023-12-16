from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from ..paginations import ListOrderPagination
from ..tasks import get_product_info, create_order
from ..utils import return_data_for_finding_intermediary, update_order_additional_info, update_order_intermediary, escape_xss_characters

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.orders.models import Order, OrderCustomerMessage, OrderIntermediaryCandidate, OrderIntermediaryCandidateMessage
from veryusefulproject.orders.api.serializers import OrderCustomerMessageSerializer, OrderIntermediaryCandidateMessageSerializer, OrderSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch


User = get_user_model()


class RequestItemInfoView(APIView):
    """
    This view is used to request information about an item from the given URL. No HTTP 
    method is allowed except POST.
    """

    permission_classes = [IsAuthenticated]
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


class OrderIntermediaryMessageCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        """
        This method is used to create a message for an order, and fully processes when
        the view receives a POST request.
        """
        
        # The following code checks if the user is authenticated.
        if not request.user.is_authenticated:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please log-in."}
            )
        
        # The following code checks if the user has provided the ID of an order and message.
        order_id = request.data.get("order_id", None)
        message = request.data.get("message", None)
        if not order_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the ID of an order."}
            )
        if not message:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide a message."}
            )

        order_qs = Order.objects.prefetch_related(
            Prefetch(
                "orderintermediarycandidate_set",
                queryset=OrderIntermediaryCandidate.objects.filter(
                    order__url_id=order_id,
                    user__username=request.user.get_username()
                ).only("created_at")
            )
        ).filter(
            url_id=order_id
        ).only(
            "url_id",
        )

        # The following code checks if the order exists.
        if not order_qs.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No order with the given order ID exists."}
            )

        # The following code checks if the user is the intermediary of the order.
        order = order_qs.first()
        intermediary = order.orderintermediarycandidate_set.all()
        if not intermediary.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No intermediary with the given username exists."}
            )

        # The following code creates the message.
        try:
            OrderIntermediaryCandidateMessage.objects.create(
                order_intermediary_candidate=intermediary.first(),
                message=escape_xss_characters(message)
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "An error occurred while creating the message."}
            )

        return Response(status=status.HTTP_201_CREATED)
        

class OrderCustomerMessageCreateView(APIView):
    """
    This view is used to create a message for an order. It requires the user to be
    authenticated. No HTTP method is allowed except POST.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        """
        This method is used to create a message for an order, and fully processes when
        the view receives a POST request.
        """
        
        # The following code checks if the user is authenticated.
        if not request.user.is_authenticated:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please log-in."}
            )
        
        # The following code checks if the user has provided the ID of an order and message.
        order_id = request.data.get("order_id", None)
        recipient = request.data.get("recipient", None)
        message = request.data.get("message", None)
        if not order_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the ID of an order."}
            )
        if not recipient:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the recipient of the message."}
            )
        if not message:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide a message."}
            )
        
        order_qs = Order.objects.select_related(
            "ordercustomerlink__customer",
        ).filter(
            url_id=order_id
        ).only(
            "ordercustomerlink__customer__username",
        )
        
        # The following code checks if the order exists.
        if not order_qs.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No order with the given order ID exists."}
            )
        order = order_qs.first()

        # The following code checks if the user is the customer of the order.
        if order.ordercustomerlink.customer.username != request.user.get_username():
            return Response(
                status=status.HTTP_403_FORBIDDEN, 
                data={"reason": "You are not authorized to perform this action."}
            )

        # The following code checks if the recipient is the intermediary of the order.
        order_intermediary = OrderIntermediaryCandidate.objects.filter(
            order=order,
            user__username=recipient
        ).only("read")
        if not order_intermediary.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No intermediary with the given username exists."}
            )
       
        # The following code creates the message.
        try:
            OrderCustomerMessage.objects.create(
                order=order,
                recipient=order_intermediary.first(),
                message=escape_xss_characters(message)
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "An error occurred while creating the message."}
            )

        return Response(status=status.HTTP_201_CREATED)


class OrderMessagesRetrieveView(RetrieveAPIView):
    """
    This view is used to retrieve all messages of an order. It requires the user to be
    authenticated. No HTTP method is allowed except GET.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """
        This method is used to retrieve all messages of an order, and fully processes when
        the view receives a GET request.
        """
        order_id = kwargs.get("pk", None)
        recipient = request.query_params.get("recipient", None)

        # The following code checks if the user is authenticated.
        if not request.user.is_authenticated:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please log-in."}
            )
        
        # The following code checks if the user has provided the ID of an order and recipient.
        if not order_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the ID of an order."}
            )
        if not recipient:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Please provide the recipient of the message."}
            )

        # The following code checks if the order exists.
        order_qs = Order.objects.prefetch_related(
            # The following code prefetches the customer messages.
            Prefetch(
                "customer_messages",
                queryset=OrderCustomerMessage.objects.filter(
                    order__url_id=order_id,
                    recipient__user__username__in=(request.user.get_username(), recipient)
                ).only(
                    "recipient",
                    "message",
                    "read",
                    "created_at"
                )
            ),
            # The following code prefetches the intermediary messages.
            Prefetch(
                "orderintermediarycandidate_set",
                queryset=OrderIntermediaryCandidate.objects.filter(
                    order__url_id=order_id,
                    user__username__in=(request.user.get_username(), recipient)
                )
            )
        ).filter(
            url_id=order_id,
            ordercustomerlink__customer__username__in=(
                request.user.get_username(), 
                recipient
            )
        ).only(
            "url_id",
        )
        
        # The following code checks if the order exists.
        if not order_qs.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No order with the given order ID exists."}
            )
        
        # The following code checks if the user is the intermediary of the order.
        order = order_qs.first()
        intermediary = order.orderintermediarycandidate_set.all()
        if not intermediary.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND, 
                data={"reason": "No intermediary with the given username exists."}
            )

        # The following code adds the customer messages to the data.
        messages = []
        customer_messages = OrderCustomerMessageSerializer(
            order.customer_messages.all(),
            many=True,
            fields=("recipient", "message", "read", "created_at")
        ).data
        messages.extend(customer_messages)

        intermediary_messages = OrderIntermediaryCandidateMessageSerializer(
            intermediary.first().intermediary_messages.all().only(
                "message", "read", "created_at"
            ),
            many=True, 
            fields=("message", "read", "created_at")
        ).data
        messages.extend(intermediary_messages)

        # The following code sorts the messages by their creation date.
        data = sorted(messages, key=lambda x: x["created_at"])
        return Response(status=status.HTTP_200_OK, data=data)


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
                return Response(status=status.HTTP_403_FORBIDDEN)
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

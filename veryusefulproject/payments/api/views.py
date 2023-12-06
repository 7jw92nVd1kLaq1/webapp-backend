from veryusefulproject.orders.models import Order
from veryusefulproject.users.api.authentication import JWTAuthentication

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from uuid import UUID

from ..tasks import generate_invoice, get_invoice


class GenerateInvoiceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        if not request.data.get("order_id", None):
            return Response(
                data={"reason": "No order_id provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = Order.objects.get(
                url_id=request.data.get("order_id"), 
                ordercustomerlink__customer=request.user
            )
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Generate invoice
        generate_invoice.delay(order.id)
        return Response(status=status.HTTP_200_OK)


class GetInvoiceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.query_params.get("order_id", None):
            return Response(
                data={"reason": "No order_id provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        order_id = request.query_params.get("order_id")
        # Check if invoice exists. If not, generate it.
        try:
            order = Order.objects.select_related(
                "orderpaymentlink__payment",
                "ordercustomerlink__customer",
                "status"
            ).only("orderpaymentlink__payment", "status__step").get(
                url_id=UUID(order_id), 
                ordercustomerlink__customer=request.user
            )
            if not order.status.step == 1:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, 
                    data={"reason": "Order is not in the correct status"}
                )
            if not order.orderpaymentlink.payment.orderpaymentinvoice_set.all().exists():
                # Generate invoice
                generate_invoice.delay(order_id)
                return Response(
                    status=status.HTTP_200_OK,
                )
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
         
        # Get invoice
        get_invoice.delay(order_id)
        return Response(status=status.HTTP_200_OK)


class ConfirmSuccessfulPaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not request.data.get("order_id", None):
            return Response(
                data={"reason": "No order_id provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = Order.objects.get(
                url_id=UUID(request.data.get("order_id"))
            )
            with transaction.atomic():
                order.set_next_status()
        except Order.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={"reason": "Order does not exist"}
            )
        except:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Confirm successful payment
        return Response(status=status.HTTP_200_OK)

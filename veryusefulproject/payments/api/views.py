from veryusefulproject.orders.models import Order
from veryusefulproject.users.api.authentication import JWTAuthentication

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


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
        return Response(status=status.HTTP_200_OK)

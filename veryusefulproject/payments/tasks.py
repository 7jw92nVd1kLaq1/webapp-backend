from veryusefulproject.orders.models import Order

from .models import OrderPaymentInvoice

from requests import get, post

from django.conf import settings
from django.db import transaction


def generate_invoice(order_id): 
    order = Order.objects.get(url_id=order_id)
    payment = order.orderpaymentlink.payment

    # Get invoice data from payment provider
    response = get(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/invoices?orderId={order_id}",
        headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}"}
    )
    if response.status_code != 200:
        # Handle error
        pass

    response_json = response.json()

    for invoice in response_json:
        if invoice["status"] != "Expired":
            # Handle error
            pass
   
     
    # Prepare data for creating invoice
    data = {
        "metadata": {
            "orderId": order_id,
        },
        "checkout": {
            "speedPolicy": "HighSpeed",
        },
    }

    # Add payment methods
    payment_methods = payment.payment_methods.all()
    data["checkout"]["paymentMethods"] = [
        payment_method.ticker for payment_method in payment_methods
    ]

    # Calculate total cost
    total_cost = payment.additional_cost
    for item in order.order_items.all():
        total_cost += item.price * item.quantity

    data["amount"] = total_cost
    data["currency"] = "USD"

    # Make a POST request to the payment provider for creating an invoice
    response = post(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/invoices",
        headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}", "Content-Type": "application/json"},
        json=data,
    )
    if response.status_code != 200:
        # Handle error
        pass
    response_json = response.json()

    with transaction.atomic():
        OrderPaymentInvoice.objects.create(
            payment=payment,
            invoice_id=response_json["id"],
            order_id=order_id,
        )

    # Send invoice information to the customer via WebSocket

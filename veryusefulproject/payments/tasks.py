from veryusefulproject.core.utils import create_command_payload_and_send
from veryusefulproject.currencies.models import CryptoCurrency
from veryusefulproject.orders.models import Order, OrderItem, OrderStatus

from config import celery_app

from .models import OrderPaymentInvoice

from datetime import datetime, timedelta
from requests import get, post
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch


@celery_app.task()
def check_if_invoices_settled():
    orders = Order.objects.filter(
        status__step=1,
        created_at__gte=datetime.now() - timedelta(days=1)
    ).select_related(
        "status",
        "orderpaymentlink__payment",
        "orderintermediarylink__intermediary"
    ).prefetch_related(
        Prefetch(
            "orderpaymentlink__payment__orderpaymentinvoice_set",
            queryset=OrderPaymentInvoice.objects.order_by("created_at").all().only("invoice_id"),
            to_attr="order_payment_invoices"
        )
    ).only(
        "url_id",
    )

    if not orders.exists():
        print("No orders found")
        return

    for order in orders:
        if not getattr(order, "orderintermediarylink", None):
            continue 
        
        payment = order.orderpaymentlink.payment
        if not payment.order_payment_invoices:
            continue

        invoice_id = payment.order_payment_invoices[-1].invoice_id
        response = get(
            f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
            f"invoices/{invoice_id}",
            headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}"}
        )
        if response.status_code != 200:
            # TODO: Log error
            continue

        response_json = response.json()
        response_status = response_json.get("status", None)
        if response_status == "Settled":
            try:
                with transaction.atomic():
                    order.set_next_status()
            except:
                pass

    print(f"Total {orders.count()} Payment status check finished")
   

@celery_app.task()
def generate_invoice(order_id):
    only = (
        "ordercustomerlink__customer__username",
        "orderpaymentlink__payment__additional_cost",
    )

    order = Order.objects.select_related(
        "ordercustomerlink__customer",
        "orderpaymentlink__payment",
    ).prefetch_related(
        Prefetch(
            "order_items",
            queryset=OrderItem.objects.filter(
                order__url_id=order_id).only("price", "quantity"),
            to_attr="order_items_list"
        ),
        Prefetch(
            "orderpaymentlink__payment__payment_methods",
            queryset=CryptoCurrency.objects.all().only("ticker"),
        )
    ).only(*only).get(url_id=UUID(order_id))

    payment = order.orderpaymentlink.payment
    channel_name = f"{order_id}#{order.ordercustomerlink.customer.get_username()}"

    # Get invoice data from payment provider
    # TODO: Add Authentication header
    response = get(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
        "invoices?orderId={order_id}",
        headers={
            "Authorization": f"token {settings.BTCPAYSERVER_TOKEN}", 
            "Content-Type": "application/json"}
    )
    if response.status_code != 200:
        print(response.json())
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice data retrieval failed"},
            channel_name
        )
        return

    response_json = response.json()
    for invoice in response_json:
        if not invoice["status"] in ("Expired", "Invalid"):
            create_command_payload_and_send(
                "publish",
                {"status_code": 400, "reason": "Valid invoice already exists"},
                channel_name
            )
            return
   
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
    for item in order.order_items_list:
        total_cost += item.price * item.quantity

    data["amount"] = str(total_cost)
    data["currency"] = "USD"

    # Make a POST request to the payment provider for creating an invoice
    response = post(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
        "invoices",
        headers={
            "Authorization": f"token {settings.BTCPAYSERVER_TOKEN}", 
            "Content-Type": "application/json"
        },
        json=data,
    )

    if response.status_code != 200:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice creation failed"},
            channel_name
        )
        return

    response_json = response.json()
    invoice_id = response_json["id"]
    response_payment_methods = get(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
        f"invoices/{invoice_id}/payment-methods",
        headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}"}
    )
    if response_payment_methods.status_code != 200:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice creation failed"},
            channel_name
        )
        return

    response_payment_methods_json = response_payment_methods.json()
    if len(response_payment_methods_json) <= 0:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice creation failed"},
            channel_name
        )
        return

    with transaction.atomic():
        OrderPaymentInvoice.objects.create(
            payment=payment,
            invoice_id=invoice_id,
            order_id=order_id,
        )

    wanted_key_from_resp_payment_methods = (
        "cryptoCode",
        "rate",
        "due",
        "payments",
        "amount",
        "totalPaid",
    )

    # Send invoice information to the customer via WebSocket
    user_data = {
        "invoice_id": response_json["id"],
        "total_cost": response_json["amount"],
        "currency": response_json["currency"],
        "invoice_created_at": response_json["createdTime"],
        "invoice_expires_at": response_json["expirationTime"],
        "payment_status": response_json["status"],
        "payment_method": dict((k, response_payment_methods_json[0][k]) 
            for k in wanted_key_from_resp_payment_methods 
                if k in response_payment_methods_json[0])
    }

    create_command_payload_and_send(
        "publish",
        {"status_code": 201, "data": user_data},
        channel_name
    )


@celery_app.task()
def get_invoice(order_id):
    order = Order.objects.select_related(
        "orderpaymentlink__payment",
        "ordercustomerlink__customer",
    ).only(
        *(
            "orderpaymentlink__payment", 
            "orderpaymentlink__payment__id",
            "ordercustomerlink__customer__username"
        )
    ).get(url_id=UUID(order_id))

    payment = order.orderpaymentlink.payment
    channel_name = f"{order_id}#{order.ordercustomerlink.customer.get_username()}"
    latest_payment_invoice = payment.orderpaymentinvoice_set.all().order_by(
        "-created_at").first()

    response = get(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
        f"invoices/{latest_payment_invoice.invoice_id}",
        headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}"}
    )
    if response.status_code != 200:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice data retrieval failed"},
            channel_name
        )
        return

    response_json = response.json()
    invoice_id = response_json["id"]
    response_payment_methods = get(
        f"{settings.BTCPAYSERVER_URL}/api/v1/stores/{settings.BTCPAYSERVER_STORE_ID}/"
        f"invoices/{invoice_id}/payment-methods",
        headers={"Authorization": f"token {settings.BTCPAYSERVER_TOKEN}"}
    )
    if response_payment_methods.status_code != 200:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice data retrieval failed"},
            channel_name
        )
        return

    response_payment_methods_json = response_payment_methods.json()
    if len(response_payment_methods_json) <= 0:
        create_command_payload_and_send(
            "publish",
            {"status_code": 400, "reason": "Invoice data retrieval failed"},
            channel_name
        )
        return

    with transaction.atomic():
        OrderPaymentInvoice.objects.create(
            payment=payment,
            invoice_id=invoice_id,
            order_id=order_id,
        )

    wanted_key_from_resp_payment_methods = (
        "cryptoCode",
        "rate",
        "due",
        "payments",
        "amount",
        "totalPaid",
    )

    user_data = {
        "invoice_id": response_json["id"],
        "total_cost": response_json["amount"],
        "currency": response_json["currency"],
        "invoice_created_at": response_json["createdTime"],
        "invoice_expires_at": response_json["expirationTime"],
        "payment_status": response_json["status"],
        "payment_method": dict((k, response_payment_methods_json[0][k]) 
            for k in wanted_key_from_resp_payment_methods 
                if k in response_payment_methods_json[0])
    }

    create_command_payload_and_send(
        "publish",
        {"status_code": 201, "data": user_data},
        channel_name
    )

import re
import requests
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from config import celery_app
from veryusefulproject.currencies.models import CryptoCurrency, FiatCurrency

from .models import Order, OrderAddress, OrderStatus, OrderAddressLink, OrderCustomerLink, OrderPaymentLink
from .utils import add_order_item, check_if_valid_url, generate_hash_hex, verify_item_hash

from veryusefulproject.core.utils import create_command_payload_and_send
from veryusefulproject.currencies.utils import convert_european_notation_to_american_notation, convert_price_to_dollar
from veryusefulproject.payments.models import OrderPayment

User = get_user_model()


@celery_app.task()
def get_product_info(url, username):
    """
    This function gets the product information from the URL and sends it to the user
    via WebSocket.
    """

    ## TODO: At every stage, send the information to a user via Websocket of the current 
    ## process of the parsing of a product.

    businessUrl = check_if_valid_url(url)
    if not businessUrl:
        raise Exception("This URL is invalid")

    resp = requests.post("http://parser:3000/", json={"url": url})
    json_data = resp.json()

    ## TODO: Separate the following code excerpt from this into new functions in .utils, 
    ## since the code below is only catering to the parsing information of Amazon 
    ## products. Add other utility functions for processing information from other 
    ## businesses as well, if necessary.

    if (json_data['price'] == "undefined"):
        raise Exception("The price of an item is unavailable")

    currency_symbol = re.search("[^\d\.\,]+", json_data["price"])
    if not currency_symbol:
        raise Exception("There is no symbol of currency in price")

    json_data["currency"] = businessUrl.currency.ticker

    price = Decimal(convert_european_notation_to_american_notation(json_data['price']))
    json_data['price'] = str(price)
    json_data['url'] = url
    json_data['domain'] = f"{businessUrl.url}dp/"

    for option in list(json_data['options'].keys()):
        if len(json_data['options'][option]) < 1:
            json_data['options'].pop(option)

    price_in_dollar = convert_price_to_dollar(url, price)
    if price_in_dollar:
        json_data["price_in_dollar"] = price_in_dollar
    elif not price_in_dollar and currency_symbol.group() != "$":
        raise Exception("Failed to convert the price of an item to dollar")

    json_data["hash"] = generate_hash_hex(json.dumps(json_data).encode("utf-8"))
    json_data["amount"] = 1

    channel_name = "{}#{}".format(username, username)
    create_command_payload_and_send("publish", {"item": json_data}, channel_name)


@celery_app.task()
def create_order(data, username):
    """
    This function creates an order based on the data sent by a user, and sends the 
    status of the process of creating an order to the user via WebSocket.
    """

    channel_name = "{}#{}".format(username, username)
    create_command_payload_and_send(
        "publish", 
        {"current_status": "0"}, 
        channel_name
    )

    if not data['value']:
        create_command_payload_and_send(
            "publish", 
            {"current_status": "-1"}, 
            channel_name
        )
        return

    addr = data['shippingAddress']
    with transaction.atomic():
        payment = OrderPayment(
            fiat_currency=FiatCurrency.objects.get(ticker="USD"),
            additional_cost=Decimal(data['additionalCost'])
        )
        payment.save()
        payment.payment_methods.add(CryptoCurrency.objects.get(ticker="BTC"))

        shipping_address, created = OrderAddress.objects.get_or_create(
            name=addr["recipient_name"],
            address1=addr["street_address1"],
            address2=addr["street_address2"],
            city=addr["city"],
            state=addr["state"],
            zipcode=addr["zipcode"],
            country=addr["country"]
        )
        order = Order.objects.create(
            status=OrderStatus.objects.get(step=1),
            additional_request=data['additionalRequest'],
        )

        OrderAddressLink.objects.create(
            order=order, 
            address=shipping_address
        )
        OrderCustomerLink.objects.create(
            order=order, 
            customer=User.objects.get(username=username)
        )
        OrderPaymentLink.objects.create(order=order, payment=payment)

        create_command_payload_and_send(
            "publish", 
            {"current_status": "1"}, 
            channel_name
        )

        for item in data['value']:
            # Check if the data of each item is tampered with
            if verify_item_hash(item.copy()):
                add_order_item(order, item)
            else:
                create_command_payload_and_send(
                    "publish", 
                    {"current_status": "-1"}, 
                    channel_name
                )
                return

        create_command_payload_and_send(
            "publish", 
            {"current_status": "2"}, 
            channel_name
        )

        print(f"Order {order.url_id} creation Completed!")

import re
import requests
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from config import celery_app
from veryusefulproject.currencies.models import CryptoCurrency, FiatCurrency

from .models import Order, OrderAddress, OrderItem, OrderStatus, OrderAddressLink, OrderCustomerLink, OrderPaymentLink
from .utils import add_order_item, check_if_valid_url, generate_hash_hex, verify_item_hash

from veryusefulproject.core.utils import create_command_payload_and_send
from veryusefulproject.currencies.utils import convert_european_notation_to_american_notation, convert_price_to_dollar
from veryusefulproject.payments.models import OrderPayment

User = get_user_model()


@celery_app.task()
def get_product_info(url, username):
    resp = requests.post("http://parser:3000/", json={"url": url})
    json_data = resp.json()

    if (json_data['price'] == "undefined"):
        return

    currency_symbol = re.search("[^\d\.\,]+", json_data["price"])
    json_data["currency"] = currency_symbol.group()

    price = Decimal(convert_european_notation_to_american_notation(json_data['price']))
    json_data['price'] = str(price)

    json_data['url'] = re.search(r"(?<=dp\/)[\w]+", url).group()

    for option in list(json_data['options'].keys()):
        if len(json_data['options'][option]) < 1:
            json_data['options'].pop(option)

    price_in_dollar = convert_price_to_dollar(currency_symbol, price)
    if price_in_dollar:
        json_data["price_in_dollar"] = price_in_dollar
    elif not price_in_dollar and currency_symbol.group() != "$":
        return

    json_data["hash"] = generate_hash_hex(json.dumps(json_data).encode("utf-8"))
    json_data["amount"] = 1

    channel_name = "{}#{}".format(username, username)
    create_command_payload_and_send("publish", {"item": json_data}, channel_name)


@celery_app.task()
def create_order(data, username):
    channel_name = "{}#{}".format(username, username)
    create_command_payload_and_send("publish", {"current_status": "0"}, channel_name)

    if not data['value']:
        create_command_payload_and_send("publish", {"current_status": "-1"}, channel_name)
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

        OrderAddressLink.objects.create(order=order, address=shipping_address)
        OrderCustomerLink.objects.create(order=order, customer=User.objects.get(username=username))
        OrderPaymentLink.objects.create(order=order, payment=payment)

        create_command_payload_and_send("publish", {"current_status": "1"}, channel_name)

        for item in data['value']:
            if verify_item_hash(item.copy()):
                print("Item has a valid hash! Yay!")
                add_order_item(order, item)
            else:
                print("Not valid hash for an item")
                create_command_payload_and_send("publish", {"current_status": "-1"}, channel_name)
                return

        create_command_payload_and_send("publish", {"current_status": "2"}, channel_name)

        print(f"Order {order.url_id} creation Completed!")

from decimal import Decimal
import re
import json

from hashlib import blake2b

from django.conf import settings

from veryusefulproject.currencies.models import FiatCurrency
from veryusefulproject.orders.models import OrderItem, OrderItemSeller, Business

AMAZON_LINK_REGEX = "(?:https?://)?(?:[a-zA-Z0-9\-]+\.)?(?:amazon|amzn){1}\.(?P<tld>[a-zA-Z\.]{2,})\/(gp/(?:product|offer-listing|customer-media/product-gallery)/|exec/obidos/tg/detail/-/|o/ASIN/|dp/|(?:[A-Za-z0-9\-]+)/dp/)?(?P<ASIN>[0-9A-Za-z]{10})"
EBAY_LINK_REGEX = "(ebay\.com\/itm\/\d+)"
SECRET_KEY_PART = settings.SECRET_KEY[:64].encode("utf-8")


def add_order_item(order, item):
    retailer = check_if_valid_url(item['domain'])
    if not retailer:
        retailer = ""

    print(f"Retailer is {retailer}")

    business = Business.objects.get(name=retailer)
    vendor, vendor_created = OrderItemSeller.objects.get_or_create(name=item["brand"])

    order_item = OrderItem.objects.create(
        order=order,
        company=business,
        seller=vendor,
        image_url=item['imageurl'],
        name=item["productName"],
        quantity=item['amount'],
        currency=FiatCurrency.objects.get(ticker="USD"),
        price=Decimal(item['price_in_dollar']) if 'price_in_dollar' in item else Decimal(item['price']),
        url=item['url'],
        options=extract_selected_options(item['options'])
    )

    print(f"{order_item.name} is successfully created!")


def check_if_valid_url(url):
    if check_if_amazon_url(url):
        return "Amazon"

    if check_if_ebay_url(url):
        return "eBay"

    return None


def check_if_amazon_url(url):
    result = re.search(AMAZON_LINK_REGEX, url)
    if result:
        return result.group()

    result = re.search(
        "^(https://)?(www.)?amazon.(com.tr)?(com.au)?(com.br)?(com)?(co.uk)?(co.jp)?(ae)?(de)?(fr)?(es)?(in)?(nl)?(pl)?(se)?(sg)?(eg)?/", url)
    if result:
        return result.group()

    return None


def check_if_ebay_url(url):
    result = re.search(EBAY_LINK_REGEX, url)
    if not result:
        return ""

    return result.group()


def convert_european_notation_to_american_notation(price):
    commaIndex = 0
    periodIndex = 0

    price = re.sub('[^\d\,\.]', '', price)

    try:
        commaIndex = price.rindex(',')
    except:
        return price

    try:
        periodIndex = price.rindex('.')
    except:
        return price.replace(',', '.')

    if commaIndex > periodIndex:
        return re.sub("[\.]", "", price).replace(",", ".")

    return price

def extract_selected_options(options):
    new_options = {}
    for key in options.keys():
        for option in options[key]:
            if "selectedOption" in option:
                new_options[key] = option
                break

    return new_options


def generate_hash_hex(data):
    h = blake2b(key=SECRET_KEY_PART, digest_size=64)
    h.update(data)
    return h.hexdigest()


def verify_item_hash(data):
    hash_value = data['hash']
    del data['hash']
    del data['amount']

    if hash_value == generate_hash_hex(json.dumps(data).encode("utf-8")):
        return True

    return False

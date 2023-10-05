from decimal import Decimal
import re
import json
from hashlib import blake2b

from veryusefulproject.currencies.models import FiatCurrency
from veryusefulproject.orders.models import OrderItem, OrderItemSeller, Business, Order, OrderIntermediaryCandidate
from veryusefulproject.orders.api.serializers import OrderSerializer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Prefetch

AMAZON_LINK_REGEX = "(?:https?://)?(?:[a-zA-Z0-9\-]+\.)?(?:amazon|amzn){1}\.(?P<tld>[a-zA-Z\.]{2,})\/(gp/(?:product|offer-listing|customer-media/product-gallery)/|exec/obidos/tg/detail/-/|o/ASIN/|dp/|(?:[A-Za-z0-9\-]+)/dp/)?(?P<ASIN>[0-9A-Za-z]{10})"
EBAY_LINK_REGEX = "(ebay\.com\/itm\/\d+)"
SECRET_KEY_PART = settings.SECRET_KEY[:64].encode("utf-8")

User = get_user_model()


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


### Functions for querying and serializing data for an order from the viewpoint of a customer

def return_data_for_finding_intermediary(order_id):
    """
    Serialize and return all the data needed for picking an intermediary of an order
    """

    only_fields = [
        "url_id",
        "created_at",
        "additional_request",
        "status__step",
        "orderaddresslink__address",
        "orderaddresslink__address__name",
        "orderaddresslink__address__address1",
        "orderaddresslink__address__address2",
        "orderaddresslink__address__city",
        "orderaddresslink__address__state",
        "orderaddresslink__address__zipcode",
        "orderaddresslink__address__country",
        "orderpaymentlink__payment",
        "orderpaymentlink__payment__fiat_currency",
        "orderpaymentlink__payment__additional_cost",
        "orderpaymentlink__payment__order_payment_balance",
        "orderpaymentlink__payment__order_payment_balance__payment_method__ticker",
    ]

    order_qs = Order.objects.prefetch_related(
        "order_items",
        Prefetch(
            "orderintermediarycandidate_set",
            queryset=OrderIntermediaryCandidate.objects.select_related("user").filter(order__url_id=order_id).only("user", "user__username"),
            to_attr="intermediary_candidates"
        )
    ).select_related(
        "orderaddresslink__address",
        "orderpaymentlink__payment__order_payment_balance__payment_method", 
        "status"
    ).filter(
        url_id=order_id
    ).only(*only_fields)

    if not order_qs.exists():
        return None

    serializer = OrderSerializer(
        order_qs.first(),
        fields=[
            "status", 
            "order_items", 
            "payment", 
            "address", 
            "url_id", 
            "created_at", 
            "orderintermediarycandidate_set", 
            "additional_request"
        ],
        context={
            "address": {"fields_exclude": ["created_at", "modified_at", "id"]},
            "order_items": {"fields": ["name", "quantity", "price", "currency", "image_url", "options"]},
            "payment": {"fields": ["fiat_currency", "additional_cost", "order_payment_balance"]},
            "order_payment_balance": {"fields": ["payment_method"]},
            "payment_method": {"fields": ["ticker", "cryptocurrencyrate_set"]},
            "cryptocurrencyrate_set": {"created_at": order_qs.first().created_at, "fields": ["rate"]},
            "orderintermediarycandidate_set": {"fields": ["user", "rate"]},
            "user": {"fields": ["username"]}
        }
    )

    data = serializer.data
    
    ## Query a list of intermediaries and each of its average ratings
    intermediaries = [intermediary['user']['username'] for intermediary in serializer.data["orderintermediarycandidate_set"]]
    users = User.objects.annotate(avg_rating=Avg("order_review_user__rating")).filter(username__in=intermediaries).only("username")
    
    for each in users:
        for index in range(len(data['orderintermediarycandidate_set'])):
            if data['orderintermediarycandidate_set'][index]['user']['username'] == each.username:
                data['orderintermediarycandidate_set'][index]['user']['average_rating'] = each.avg_rating
                break
                  
    return data 


def return_data_for_deposit_status(order_id):
    deferred_fields = [
        "status__name",
        "status__desc",
        "status__created_at",
        "status__modified_at",
        "orderaddresslink__created_at",
        "orderaddresslink__modified_at",
        "orderpaymentlink__created_at",
        "orderpaymentlink__modified_at",
        "orderpaymentlink__payment__fiat_currency",
        "orderpaymentlink__payment__discount",
        "orderpaymentlink__payment__created_at",
        "orderpaymentlink__payment__modified_at",
    ]
    order_qs = Order.objects.prefetch_related("order_items").select_related(
        "orderaddresslink__address", 
        "orderpaymentlink__payment__order_payment_balance__payment_method", 
        "status"
    ).filter(
        url_id=order_id
    ).defer(*deferred_fields)

    if not order_qs.exists():
        return {}

    serializer = OrderSerializer(
        order_qs.first(),
        fields_exclude=[
            "customer",
            "intermediary",
            "orderdispute_set",
            "messages",
            "order_reviews"
        ],
        context={
            "address": {"fields": ["address"]},
            "payment": {"fields_exclude": ["discount", "fiat_currency", "created_at", "modified_at"]},
            "order_items": {"fields_exclude": ["tracking", "order_identifier", "order", "created_at", "modified_at"]},
            "order_payment_balance": {"fields": ["payment_method", "deposit_address", "balance"]},
            "payment_method": {"fields": ["ticker", "name", "cryptocurrencyrate_set"]},
            "cryptocurrencyrate_set": {"created_at": order_qs.first().created_at, "fields": ["rate"]}
        }
    )

    return serializer.data

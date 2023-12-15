from decimal import Decimal
import re
import json
from hashlib import blake2b

from veryusefulproject.currencies.models import FiatCurrency
from veryusefulproject.orders.models import BusinessUrl, OrderItem, OrderItemSeller, Order, OrderIntermediaryCandidate, OrderIntemediaryCandidateOffer, OrderAddress, OrderIntermediaryLink, OrderStatus
from veryusefulproject.orders.api.serializers import OrderSerializer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Prefetch
from django.utils.html import escape

from rest_framework import status
from rest_framework.response import Response

AMAZON_LINK_REGEX = "^(?:https?://)?(?:[a-zA-Z0-9\-]+\.)?(?:amazon|amzn){1}\.(com\.au|" \
        "com|co\.uk|co\.jp|de|fr|es|in)\/(gp/(?:product|offer-listing|customer-media/" \
        "product-gallery)/|exec/obidos/tg/detail/-/|o/ASIN/|dp/|(?:[A-Za-z0-9\-]+)/dp/" \
        ")?(?P<ASIN>[0-9A-Za-z]{10})"
EBAY_LINK_REGEX = "(ebay\.com\/itm\/\d+)"
SECRET_KEY_PART = settings.SECRET_KEY[:64].encode("utf-8")

User = get_user_model()


def add_order_item(order, item):
    businessUrl = check_if_valid_url(item['url'])
    if not businessUrl:
        raise Exception("There is no business with that domain name.")

    vendor, vendor_created = OrderItemSeller.objects.get_or_create(name=item["brand"])

    OrderItem.objects.create(
        order=order,
        website_domain=businessUrl,
        seller=vendor,
        image_url=item['imageurl'],
        name=item["productName"],
        quantity=item['amount'],
        currency=FiatCurrency.objects.get(ticker="USD"),
        price=Decimal(item['price_in_dollar']) if 'price_in_dollar' in item else Decimal(item['price']),
        url=item['url'],
        options=extract_selected_options(item['options'])
    )


def check_if_valid_url(url):
    if check_if_amazon_url(url):
        try:
            businessURL = get_businessUrl_amazon(url)
            return businessURL
        except Exception as e:
            print(e)

    return None


def check_if_amazon_url(url):
    result = re.search(AMAZON_LINK_REGEX, url)
    if result:
        return result.group()

    return None


def get_businessUrl_amazon(url):
    regex = "(?:amazon|amzn){1}\.(com\.au|com|co\.uk|co\.jp|de|fr|es|in)"
    result = re.search(regex, url)
    if result:
        return BusinessUrl.objects.select_related("currency").filter(
            url__contains=result.group()).order_by("-currency__ticker").first()

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
    try:
        hash_value = data['hash']
        del data['hash']
        del data['amount']

        if hash_value == generate_hash_hex(json.dumps(data).encode("utf-8")):
            return True
    except:
        return False


def escape_xss_characters(string):
    return escape(string)


# Functions for querying and serializing data for an order from the viewpoint of a customer

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
    ]

    order_qs = Order.objects.prefetch_related(
        "order_items",
        Prefetch(
            "orderintermediarycandidate_set",
            queryset=OrderIntermediaryCandidate.objects.prefetch_related(
                Prefetch(
                    "offers",
                    queryset=OrderIntemediaryCandidateOffer.objects.filter(
                        order_intermediary_candidate__order__url_id=order_id
                    ).only("rate", "created_at")
                )
            ).select_related("user").filter(
                order__url_id=order_id
            ).only(
                "user", 
                "user__username", 
                "created_at"
            ).order_by(
                "-created_at"
            ),
        )
    ).select_related(
        "orderaddresslink__address",
        "orderpaymentlink__payment",
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
            "order_items": {
                "fields": [
                    "name", 
                    "quantity", 
                    "price", 
                    "currency", 
                    "image_url", 
                    "options"
                ]
            },
            "payment": {
                "fields_exclude": [
                    "orderpaymentinvoice_set", 
                    "created_at", 
                    "modified_at"
                ]
            },
            "payment_methods": {
                "fields": ["ticker", "cryptocurrencyrate_set"]
            },
            "cryptocurrencyrate_set": {
                "created_at": order_qs.first().created_at, 
                "fields": ["rate"]
            },
            "orderintermediarycandidate_set": {
                "fields": [
                    "user", 
                    "created_at", 
                    "accepted",
                    "offers"
                ]
            },
            "offers": {
                "fields": ["rate", "created_at"]
            },
            "user": {"fields": ["username"]}
        }
    )

    data = serializer.data

    ## Query a list of intermediaries and each of its average ratings
    intermediaries = list(intermediary['user']['username'] 
        for intermediary in data["orderintermediarycandidate_set"]
    )
    users = User.objects.annotate(
        avg_rating=Avg("order_review_user__rating"),
        review_count=Count("order_review_user")
    ).filter(username__in=intermediaries).only("username")

    ## Add the average ratings to the data
    for intermediary in range(len(data["orderintermediarycandidate_set"])):
        for user in users:
            if data["orderintermediarycandidate_set"][intermediary]["user"]["username"] == user.username:
                data["orderintermediarycandidate_set"][
                    intermediary
                ]["user"]["avg_rating"] = user.avg_rating

                data["orderintermediarycandidate_set"][
                    intermediary
                ]["user"]["review_count"] = user.review_count

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
        "orderpaymentlink__payment",
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
            "payment": {"fields_exclude": ["created_at", "modified_at"]},
            "order_items": {
                "fields_exclude": [
                    "tracking", 
                    "order_identifier", 
                    "order", 
                    "created_at", 
                    "modified_at"
                ]
            },
            "invoice": {"fields": ["invoice_id"]},
            "payment_methods": {"fields": ["ticker", "name", "cryptocurrencyrate_set"]},
            "cryptocurrencyrate_set": {
                "created_at": order_qs.first().created_at, 
                "fields": ["rate"]
            }
        }
    )

    return serializer.data


def update_order_additional_info(order, data):
    if order.status.step != 1:
        return Response(
            status=status.HTTP_400_BAD_REQUEST, 
            data={
                "reason": "You can't update the additional information of this order,"  
                "since it has progressed past the step of finding an intermediary."
            }
        )

    if not data.get("additional_request", None) and not data.get("address", None):
        return Response(
            status=status.HTTP_400_BAD_REQUEST, 
            data={
                "reason": "Please provide the additional information you want to" 
                " update. You can update either the additional request or the address."
            }
        )

    with transaction.atomic():
        if data.get("additional_request", None):
            order.additional_request = escape_xss_characters(data.get("additional_request"))
            order.save()

        if data.get("address", None):
            for key in data["address"].keys():
                data["address"][key] = escape_xss_characters(data["address"][key])

            OrderAddress.objects.filter(id=order.orderaddresslink.address.id).update(**data["address"])

    return Response(
        status=status.HTTP_200_OK, 
        data=return_data_for_finding_intermediary(order.url_id)
    )


def update_order_intermediary(order, data):
    """
    This assigns an intermediary to an order. The parameter \"data\" must be of \"dict\" 
    type and contain the \"username\" of an intermediary.
    """

    ## TODO: Separate this method from the view.
    if not data.get("username", None):
        return Response(
            status=status.HTTP_400_BAD_REQUEST, 
            data={"reason": "Please provide the username of an intermediary you chose."}
        )

    candidate = OrderIntermediaryCandidate.objects.select_related("user").filter(
        order=order, 
        user__username=data.get("username")
    )

    if not candidate.exists():
        return Response(
            status=status.HTTP_400_BAD_REQUEST, 
            data={
                "reason": "The username you provided is not a part of candidates of this order."
            }
        )

    with transaction.atomic():
        try:
            OrderIntermediaryLink.objects.create(
                order=order, 
                intermediary=candidate.first().user
            )
        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={
                    "reason": "An error has occurred while assigning a candidate"
                    "to an intermediary of this order. Please try again."
                }
            )

        order.status = OrderStatus.objects.get(step=order.status.step+1)
        order.save()

        data = return_data_for_deposit_status(order.url_id)
        return Response(status=status.HTTP_201_CREATED, data=data)

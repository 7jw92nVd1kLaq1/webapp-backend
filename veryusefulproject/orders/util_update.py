from veryusefulproject.orders.models import Order, OrderIntermediaryCandidate
from django.db.models import Avg, Prefetch


def return_data_for_finding_intermediary(self, order_id):
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

    serializer = self.get_serializer_class()(
        order_qs.first(),
        fields=["status", "order_items", "payment", "address", "url_id", "created_at", "orderintermediarycandidate_set", "additional_request"],
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


def return_data_for_deposit_status(self, order_id):
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

    serializer = self.get_serializer_class()(
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


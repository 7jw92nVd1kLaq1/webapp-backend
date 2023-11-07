from django.contrib.auth import get_user_model

from veryusefulproject.orders.models import Order, OrderIntermediaryCandidate

MODEL_MAP = {}

USER_MODEL_MAP = {
    'User': get_user_model(),
}

ORDER_MODEL_MAP = {
    'Order': Order,
    'OrderIntermediaryCandidate': OrderIntermediaryCandidate,
}

MODEL_MAP.update(USER_MODEL_MAP)
MODEL_MAP.update(ORDER_MODEL_MAP)


MODEL_UNIQUE_IDENTIFIER_FIELD_MAP = {
    "Order": "url_id",
    "User": "username",
}

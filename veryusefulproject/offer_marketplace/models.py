from django.contrib.auth import get_user_model
from django.db import models

from veryusefulproject.currencies.models import CryptoCurrency, FiatCurrency
from veryusefulproject.core.models import BaseModel


User = get_user_model()


class IntermediaryOfferStatus(BaseModel):
    name = models.CharField(max_length=128)
    desc = models.TextField()


class IntermediaryOffer(BaseModel):
    status = models.ForeignKey(IntermediaryOfferStatus, on_delete=models.RESTRICT)
    intermediary = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name="intermediary_offer_intermediary")
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name="intermediary_offer_customer")
    min_offer_price = models.FloatField()
    max_offer_price = models.FloatField()
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.RESTRICT)
    cryptocurrency = models.ForeignKey(CryptoCurrency, on_delete=models.RESTRICT)
    desc = models.TextField()


class IntermediaryOfferNegotiation(BaseModel):
    offer = models.ForeignKey(IntermediaryOffer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class IntermediaryOfferNegotiationItem(BaseModel):
    negotiation = models.ForeignKey(IntermediaryOfferNegotiation, on_delete=models.CASCADE)
    image_url = models.URLField()
    name = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    url = models.URLField()
    options = models.JSONField()


class IntermediaryOfferNegotiationMessage(BaseModel):
    negotiation = models.ForeignKey(IntermediaryOfferNegotiation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()


class IntermediaryOfferNegotiationOffer(BaseModel):
    negotiation = models.ForeignKey(IntermediaryOfferNegotiation, on_delete=models.CASCADE)
    price = models.FloatField()

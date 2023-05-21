from django.db import models

from veryusefulproject.core.models import BaseModel
from veryusefulproject.currencies.models import CryptoCurrency, FiatCurrency

# Create your models here.


class OrderPaymentBalance(BaseModel):
    deposit_address = models.TextField()
    payment_method = models.ForeignKey(
        CryptoCurrency,
        on_delete=models.RESTRICT,
        related_name="payment_method")
    balance = models.FloatField()


class OrderPayment(BaseModel):
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    order_payment_balance = models.OneToOneField(OrderPaymentBalance, on_delete=models.RESTRICT)
    discount = models.FloatField()
    additional_cost = models.FloatField()

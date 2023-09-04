from decimal import Decimal

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
    balance = models.DecimalField(max_digits=19, decimal_places=10)


class OrderPayment(BaseModel):
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    order_payment_balance = models.OneToOneField(OrderPaymentBalance, on_delete=models.RESTRICT)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))

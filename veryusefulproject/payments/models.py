from decimal import Decimal

from django.db import models

from veryusefulproject.core.models import BaseModel
from veryusefulproject.currencies.models import CryptoCurrency, FiatCurrency

# Create your models here.

class OrderPayment(BaseModel):
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    payment_methods = models.ManyToManyField(CryptoCurrency)


class OrderPaymentInvoice(BaseModel):
    payment = models.ForeignKey(OrderPayment, on_delete=models.CASCADE)
    invoice_id = models.TextField()
    order_id = models.TextField()


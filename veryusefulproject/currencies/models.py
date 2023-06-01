from django.db import models
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from veryusefulproject.core.models import BaseModel

# Create your models here.


def alphabetValidator(value):
    if not value.isalpha():
        raise ValidationError(
            _("The ticker contains something other than alphabet characters.")
        )


class Currency(BaseModel):
    ticker: models.CharField = models.CharField(
        max_length=5, validators=[alphabetValidator], primary_key=True, default=get_random_string(5))
    desc: models.TextField = models.TextField(default="")
    rate: models.FloatField = models.FloatField(default=0.0)


class FiatCurrency(Currency):
    name: models.CharField = models.CharField(max_length=128, validators=[alphabetValidator])


class FiatCurrencyRate(BaseModel):
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE, null=True)
    rate = models.FloatField()


class CryptoCurrency(Currency):
    name: models.CharField = models.CharField(max_length=128)


class CryptoCurrencyRate(BaseModel):
    cryptocurrency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE, null=True)
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.RESTRICT, null=True)
    rate = models.FloatField()

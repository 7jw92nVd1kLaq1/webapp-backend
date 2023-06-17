from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from veryusefulproject.core.models import BaseModel

# Create your models here.


def alphabetValidator(value):
    if not value.isalpha():
        raise ValidationError(
            _("The ticker contains something other than alphabet characters.")
        )


class FiatCurrency(BaseModel):
    ticker: models.CharField = models.CharField(
        max_length=5, validators=[alphabetValidator], primary_key=True)
    desc: models.TextField = models.TextField()
    name: models.CharField = models.CharField(max_length=128, validators=[alphabetValidator])


class FiatCurrencyRate(BaseModel):
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    rate = models.FloatField()


class CryptoCurrency(BaseModel):
    ticker: models.CharField = models.CharField(
        max_length=5, validators=[alphabetValidator], primary_key=True)
    desc: models.TextField = models.TextField()
    name: models.CharField = models.CharField(max_length=128)


class CryptoCurrencyRate(BaseModel):
    cryptocurrency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE)
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.RESTRICT)
    rate = models.FloatField()

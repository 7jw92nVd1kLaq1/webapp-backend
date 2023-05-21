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


class Currency(BaseModel):
    ticker: models.CharField = models.CharField(max_length=5, validators=[alphabetValidator], primary_key=True)
    desc: models.TextField = models.TextField()
    rate: models.FloatField = models.FloatField()


class FiatCurrency(Currency):
    name: models.CharField = models.CharField(max_length=128, validators=[alphabetValidator])


class CryptoCurrency(Currency):
    name: models.CharField = models.CharField(max_length=128)
    fiat_currency: models.ForeignKey = models.ForeignKey(
        FiatCurrency,
        models.SET_NULL,
        null=True,
        related_name="FiatCurrency_PK")

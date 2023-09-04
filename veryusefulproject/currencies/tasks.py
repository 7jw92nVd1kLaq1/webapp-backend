from config import celery_app
from django.db import transaction

from veryusefulproject.currencies.models import CryptoCurrency, CryptoCurrencyRate, FiatCurrency, FiatCurrencyRate

import requests
from decimal import Decimal

@celery_app.task()
def update_currency_info():
    resp = requests.get("http://parser:3000/getCurrencyData/")
    json = resp.json()

    for currency in json:
        try:
            fiat_currency, created = FiatCurrency.objects.get_or_create(ticker=currency["ticker"], desc="", name=currency["name"])
            currency_rate = FiatCurrencyRate.objects.create(fiat_currency=fiat_currency, rate=Decimal(currency["rateAgainstDollar"]))
        except Exception as e:
            print("Error occurred at {}".format(currency))
            print(e)

@celery_app.task()
def update_crypto_currency_info():
    with transaction.atomic():
        for currency in CryptoCurrency.objects.all():
            resp = requests.post("http://parser:3000/getCryptoCurrencyData/", json={"name": currency.name, "ticker": currency.ticker})
            json = resp.json()
            
            print(f"Price of {currency.ticker} is ${json['rate']}")
            CryptoCurrencyRate.objects.create(cryptocurrency=currency, fiat_currency=FiatCurrency.objects.get(ticker="USD"), rate=Decimal(json['rate']))

    print("Price Successfully Updated!")

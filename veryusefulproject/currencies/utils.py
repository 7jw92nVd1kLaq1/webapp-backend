import re

from django.db.models import Q

from .models import CryptoCurrency, FiatCurrency, FiatCurrencyRate
from veryusefulproject.orders.utils import get_businessUrl_amazon

def convert_european_notation_to_american_notation(price):
    commaIndex = 0
    periodIndex = 0

    price = re.sub('[^\d\,\.]', '', price)

    try:
        commaIndex = price.rindex(',')
    except:
        return price

    try:
        periodIndex = price.rindex('.')
    except:
        return price.replace(',', '.')

    if commaIndex > periodIndex:
        return re.sub("[\.]", "", price).replace(",", ".")
    
    return price


def convert_price_to_dollar(url, price):
    businessUrl = get_businessUrl_amazon(url)
    if businessUrl.currency.ticker == "USD":
        return None

    if businessUrl:
        conversion_rate_against_dollar = FiatCurrencyRate.objects.filter(fiat_currency=businessUrl.currency).order_by("created_at").last().rate
        return str(price / conversion_rate_against_dollar)

    return None



def get_orders_cryptocurrency_rate(datetime_str, cryptocurrency_ticker):
    cryptocurrency = CryptoCurrency.objects.get(ticker=cryptocurrency_ticker)
    cryptocurrency_rate = cryptocurrency.cryptocurrencyrate_set.filter(
       Q(created_at__lte=datetime_str) 
    ).order_by("-created_at").only("rate").first()

    return float(cryptocurrency_rate.rate)

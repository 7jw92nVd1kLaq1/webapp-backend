import re

from .models import FiatCurrency, FiatCurrencyRate

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


def convert_price_to_dollar(symbol, price):
    if symbol and symbol.group() != "$":
        symbol = symbol.group().encode("utf-8")
        qs = FiatCurrency.objects.filter(symbol=symbol)
        if qs.exists():
            conversion_rate_against_dollar = FiatCurrencyRate.objects.filter(fiat_currency=qs.first()).order_by("created_at")
            return str(price / conversion_rate_against_dollar.last().rate)

    return ""

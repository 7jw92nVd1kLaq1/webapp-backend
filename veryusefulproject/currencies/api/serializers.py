from rest_framework import serializers

from ..models import CryptoCurrency, FiatCurrency


class FiatCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FiatCurrency


class CryptoCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCurrency

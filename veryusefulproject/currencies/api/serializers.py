from rest_framework import serializers

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from ..models import CryptoCurrency, FiatCurrency, CryptoCurrencyRate, FiatCurrencyRate

class CryptoCurrencyRateSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CryptoCurrencyRate
        fields = "__all__"


class FiatCurrencyRateSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = FiatCurrencyRate
        fields = "__all__"


class FiatCurrencySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = FiatCurrency
        fields = "__all__"


class CryptoCurrencySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    cryptocurrencyrate_set = serializers.SerializerMethodField()

    class Meta:
        model = CryptoCurrency
        fields = "__all__"

    def get_cryptocurrencyrate_set(self, obj):
        context = self.context.get("cryptocurrencyrate_set")
        if not context:
            return None

        order_creation_time = context.pop("created_at", None)
        obj = obj.cryptocurrencyrate_set.filter(created_at__lte=order_creation_time).order_by("created_at").last()
        serializer = CryptoCurrencyRateSerializer(obj, **context)
        return serializer.data

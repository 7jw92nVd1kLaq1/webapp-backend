from rest_framework import serializers

from ..models import OrderPayment, OrderPaymentBalance

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from veryusefulproject.currencies.api.serializers import CryptoCurrencySerializer


class OrderPaymentBalanceSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = OrderPaymentBalance
        fields = "__all__"

    def get_payment_method(self, obj):
        context = self.context.get("payment_method", {})
        serializer = CryptoCurrencySerializer(obj.payment_method, context=self.context, **context)
        return serializer.data


class OrderPaymentSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    order_payment_balance = serializers.SerializerMethodField()

    class Meta:
        model = OrderPayment
        fields = "__all__"

    def get_order_payment_balance(self, obj):
        context = self.context.get("order_payment_balance", {})
        serializer = OrderPaymentBalanceSerializer(obj.order_payment_balance, context=self.context, **context)

        return serializer.data

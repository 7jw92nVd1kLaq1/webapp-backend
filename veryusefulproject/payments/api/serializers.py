from rest_framework import serializers

from ..models import OrderPayment, OrderPaymentInvoice

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from veryusefulproject.currencies.api.serializers import CryptoCurrencySerializer


class OrderPaymentInvoiceSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentInvoice
        fields = "__all__"


class OrderPaymentSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    orderpaymentinvoice_set = serializers.SerializerMethodField()
    payment_methods = serializers.SerializerMethodField()

    class Meta:
        model = OrderPayment
        fields = "__all__"

    def get_payment_methods(self, obj):
        context = self.context.get("payment_method", {})
        serializer = CryptoCurrencySerializer(obj.payment_methods.all(), many=True, context=self.context, **context)
        return serializer.data

    def get_orderpaymentinvoice_set(self, obj):
        context = self.context.get("invoice", {})
        serializer = OrderPaymentInvoiceSerializer(obj.orderpaymentinvoice_set.all(), many=True, context=self.context, **context)

        return serializer.data

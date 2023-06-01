from rest_framework import serializers

from ..models import OrderPayment, OrderPaymentBalance


class OrderPaymentBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentBalance
        read_only_fields = ['payment_method']


class OrderPaymentSerializer(serializers.ModelSerializer):
    order_payment_balance = OrderPaymentBalanceSerializer(many=False)

    class Meta:
        model = OrderPayment
        read_only_fields = ['fiat_currency', 'order_payment_balance']

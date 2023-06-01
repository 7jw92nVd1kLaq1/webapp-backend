from rest_framework import serializers

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from veryusefulproject.orders.models import Business, BusinessIndustry, BusinessLogo, Order, OrderAddress, OrderDispute, OrderDisputeMessage, OrderIntermediaryBlacklist, OrderItem, OrderMessage, OrderReview, OrderStatus, OrderTrackingNumber
from veryusefulproject.payments.api.serializers import OrderPaymentSerializer


class BusinessLogoSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    business = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = BusinessLogo


class BusinessSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    industry = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = Business
        fields = ["ticker", "name", "industry"]


class BusinessIndustrySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    businesses = BusinessSerializer(many=True)

    class Meta:
        model = BusinessIndustry
        fields = ["id", "name", "businesses"]


class OrderAddressSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = '__all__'


class OrderDisputeMessageSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderDisputeMessage
        fields = '__all__'


class OrderDisputeSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    order = serializers.SlugRelatedField(slug_field="url_id", read_only=True)
    messages = OrderDisputeMessageSerializer(many=True)

    class Meta:
        model = OrderDispute
        fields = '__all__'


class OrderIntermediaryBlacklistSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderIntermediaryBlacklist
        fields = '__all__'


class OrderItemSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderReviewSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = OrderReview
        fields = '__all__'


class OrderStatusSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = '__all__'


class OrderTrackingNumberSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    shipping_company = serializers.SlugRelatedField(slug_field="ticker", read_only=True)

    class Meta:
        model = OrderTrackingNumber
        fields = '__all__'


class OrderMessageSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = OrderMessage
        exclude = ['order']


class OrderSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    status = serializers.SlugRelatedField(slug_field="name", read_only=True)
    company = serializers.SlugRelatedField(slug_field="name", read_only=True)
    payment = OrderPaymentSerializer()
    address = OrderAddressSerializer()
    customer = serializers.SlugRelatedField(slug_field="username", read_only=True)
    intermediary = serializers.SlugRelatedField(slug_field="username", read_only=True)
    tracking = OrderTrackingNumberSerializer()
    messages = OrderMessageSerializer(many=True)
    dispute = OrderDisputeSerializer(required=False)
    order_items = OrderItemSerializer(many=True)
    order_reviews = OrderReviewSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'

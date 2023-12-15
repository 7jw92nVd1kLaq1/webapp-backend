from rest_framework import serializers

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from veryusefulproject.orders.models import Business, BusinessLogo, Order, OrderAddress, OrderAddressLink, OrderCustomerLink, OrderDispute, OrderDisputeMessage, OrderIntermediaryCandidate, OrderIntermediaryLink, OrderItem, OrderCustomerMessage, OrderPaymentLink, OrderReview, OrderStatus, OrderTrackingNumber, OrderIntermediaryCandidateMessage, OrderIntemediaryCandidateOffer
from veryusefulproject.payments.api.serializers import OrderPaymentSerializer
from veryusefulproject.users.api.serializers import UserSerializer


class BusinessLogoSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    business = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = BusinessLogo


class BusinessSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["ticker", "name"]



class OrderAddressSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = '__all__'


class OrderAddressLinkSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    address = serializers.SerializerMethodField("get_address")

    class Meta:
        model = OrderAddressLink
        fields = '__all__'

    def get_address(self, obj):
        addr_obj = obj.address
        context = self.context.get("address", {})
        serializer = OrderAddressSerializer(addr_obj, **context)
        return serializer.data


class OrderCustomerLinkSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    customer = serializers.SerializerMethodField("get_customer")

    class Meta:
        model = OrderCustomerLink
        fields = "__all__"

    def get_customer(self, obj):
        customer_obj = obj.customer
        context = self.context.get("customer", {})
        serializer = UserSerializer(customer_obj, **context)
        return serializer.data


class OrderIntermediaryLinkSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    intermediary = serializers.SerializerMethodField("get_intermediary")

    class Meta:
        model = OrderIntermediaryLink
        fields = "__all__"

    def get_intermediary(self, obj):
        intermediary_obj = obj.intermediary
        context = self.context.get("user", {})
        serializer = UserSerializer(intermediary_obj, **context)
        return serializer.data


class OrderDisputeMessageSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderDisputeMessage
        fields = '__all__'


class OrderDisputeSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    order = serializers.SlugRelatedField(slug_field="url_id", read_only=True)

    class Meta:
        model = OrderDispute
        fields = '__all__'


class OrderIntermediaryCandidateSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    intermediary_messages = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderIntermediaryCandidate
        fields = '__all__'

    def get_offers(self, obj):
        context = self.context.get("offers", {})
        serializer = OrderIntermediaryCandidateOfferSerializer(
            obj.offers.all(),
            many=True, 
            context=self.context,
            **context
        )
        return serializer.data

    def get_intermediary_messages(self, obj):
        context = self.context.get("intermediary_messages", {})
        serializer = OrderIntermediaryCandidateMessageSerializer(
            obj.intermediary_messages.all(),
            many=True, 
            context=self.context,
            **context
        )
        return serializer.data

    def get_user(self, obj):
        context = self.context.get("user", {})
        serializer = UserSerializer(obj.user, context=self.context, **context)
        return serializer.data


class OrderItemSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderReviewSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = OrderReview
        fields = '__all__'
    
    def get_user(self, obj):
        context = self.context.get("order_reviews__user", {})
        serializer = UserSerializer(obj.user, **context)
        return serializer.data

    
class OrderStatusSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = '__all__'


class OrderTrackingNumberSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    shipping_company = serializers.SlugRelatedField(slug_field="ticker", read_only=True)

    class Meta:
        model = OrderTrackingNumber
        fields = '__all__'


class OrderCustomerMessageSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = OrderCustomerMessage
        exclude = ['order']


class OrderIntermediaryCandidateOfferSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderIntemediaryCandidateOffer
        exclude = ['order_intermediary_candidate']


class OrderIntermediaryCandidateMessageSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderIntermediaryCandidateMessage
        exclude = ['order_intermediary_candidate']


class OrderPaymentLinkSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    payment = serializers.SerializerMethodField("get_payment")

    class Meta:
        model = OrderPaymentLink
        fields = "__all__"

    def get_payment(self, obj):
        payment_obj = obj.payment
        context = self.context.get("payment", {})
        serializer = OrderPaymentSerializer(payment_obj, context=self.context, **context)
        return serializer.data


class OrderSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    status = serializers.SlugRelatedField(slug_field="step", read_only=True)
    address = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    intermediary = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    orderdispute_set = OrderDisputeSerializer(fields_exclude=['order', 'mediator'])
    order_items = serializers.SerializerMethodField()
    order_reviews = serializers.SerializerMethodField()
    orderintermediarycandidate_set = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_orderintermediarycandidate_set(self, obj):
        context = self.context.get("orderintermediarycandidate_set", {})
        serializer = OrderIntermediaryCandidateSerializer(
            obj.orderintermediarycandidate_set.all(),
            many=True, 
            context=self.context,
            **context
        )
        return serializer.data 

    def get_order_items(self, obj):
        context = self.context.get("order_items", {})
        serializer = OrderItemSerializer(
            obj.order_items.all(), 
            many=True, 
            **context
        )
        return serializer.data

    def get_order_reviews(self, obj):
        context = self.context.get("order_reviews", {})
        serializer = OrderReviewSerializer(
            obj.order_reviews.all(), 
            many=True, 
            **context
        )
        return serializer.data

    def get_address(self, obj):
        if not hasattr(obj, "orderaddresslink"):
            return None

        serializer = OrderAddressLinkSerializer(
            obj.orderaddresslink, 
            fields=["address"], 
            context=self.context
        )
        return serializer.data

    def get_customer(self, obj):
        if not hasattr(obj, "ordercustomerlink"):
            return None

        serializer = OrderCustomerLinkSerializer(
            obj.ordercustomerlink, 
            fields=['customer'], 
            context=self.context
        )
        return serializer.data

    def get_intermediary(self, obj):
        if not hasattr(obj, "orderintermediarylink"):
            return None

        serializer = OrderIntermediaryLinkSerializer(
            obj.orderintermediarylink, 
            fields=["intermediary"], 
            context=self.context
        )
        return serializer.data

    def get_payment(self, obj):
        if not hasattr(obj, "orderpaymentlink"):
            return None
        
        serializer = OrderPaymentLinkSerializer(
            obj.orderpaymentlink, 
            fields=["payment"], 
            context=self.context
        )
        return serializer.data

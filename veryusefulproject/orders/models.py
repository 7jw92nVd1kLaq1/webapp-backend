from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.validators import validate_slug
from django.db import models
from django.utils.html import escape

from veryusefulproject.core.models import BaseModel
from veryusefulproject.payments.models import OrderPayment
from veryusefulproject.shipping.models import ShippingCompany


User = get_user_model()


class BusinessIndustry(BaseModel):
    name = models.CharField(max_length=128)
    desc = models.TextField()


class Business(BaseModel):
    ticker = models.CharField(max_length=16, primary_key=True)
    industry = models.ForeignKey(BusinessIndustry, related_name="businesses", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=64)
    desc = models.TextField()


class BusinessLogo(BaseModel):
    business = models.ForeignKey(Business, related_name="logos", on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to="images/logo/%Y/%m/%d")


class OrderAddress(BaseModel):
    name = models.TextField()
    address1 = models.TextField()
    address2 = models.TextField(default="")
    city = models.TextField()
    state = models.TextField()
    zipcode = models.TextField()
    country = models.TextField()


class OrderStatus(BaseModel):
    name = models.CharField(max_length=128, unique=True, validators=[validate_slug])
    desc = models.TextField()


class OrderTrackingNumber(BaseModel):
    tracking_number = models.CharField(max_length=128, validators=[validate_slug])
    shipping_company = models.ForeignKey(ShippingCompany, on_delete=models.RESTRICT, null=True)


class Order(BaseModel):
    url_id = models.UUIDField(default=uuid4)
    status = models.ForeignKey(OrderStatus, on_delete=models.RESTRICT)
    company = models.ForeignKey(Business, on_delete=models.RESTRICT)
    payment = models.OneToOneField(OrderPayment, on_delete=models.RESTRICT)
    address = models.ForeignKey(OrderAddress, on_delete=models.RESTRICT)
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_customer")
    intermediary = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_intermediary")
    tracking = models.OneToOneField(OrderTrackingNumber, on_delete=models.SET_NULL, null=True)
    additional_request = models.TextField(default="")

    def set_additional_request(self, value):
        self.additional_request = escape(value)


class OrderDispute(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT)
    mediator = models.ManyToManyField(User)


class OrderDisputeMessage(BaseModel):
    order_dispute = models.ForeignKey(OrderDispute, on_delete=models.RESTRICT)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()


class OrderMessage(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    image_url = models.URLField()
    name = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    url = models.URLField()
    options = models.JSONField()


class OrderIntermediaryBlacklist(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)


class OrderReview(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_review_user")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_review_author")
    title = models.TextField()
    content = models.TextField()
    rating = models.FloatField()
    upvote = models.PositiveIntegerField()
    downvote = models.PositiveIntegerField()

    def set_title(self, title) -> None:
        self.title = escape(title)

    def set_content(self, content) -> None:
        self.content = escape(content)

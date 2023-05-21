from django.db import models

from veryusefulproject.core.models import BaseModel
from veryusefulproject.orders.models import Business
from veryusefulproject.users.models import User
from veryusefulproject.currencies.models import FiatCurrency

# Create your models here.


class Cart(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    fiat_currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    retailer = models.ForeignKey(Business, on_delete=models.RESTRICT)
    image_url = models.URLField()
    name = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    url = models.URLField()
    options = models.JSONField()

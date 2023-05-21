from django.db import models

from veryusefulproject.core.models import BaseModel


class ShippingCompany(BaseModel):
    ticker = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=128)
    desc = models.TextField()

from rest_framework import serializers

from ..models import ShippingCompany


class ShippingCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingCompany

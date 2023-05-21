from rest_framework import serializers

from veryusefulproject.orders.models import Business, BusinessIndustry


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        field = ["ticker", "desc", "name"]


class BusinessIndustrySerializer(serializers.ModelSerializer):
    businesses = BusinessSerializer(many=True, read_only=True)

    class Meta:
        model = BusinessIndustry
        fields = ["name", "desc", "businesses"]

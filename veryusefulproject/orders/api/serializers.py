from rest_framework import serializers

from veryusefulproject.orders.models import Business, BusinessIndustry, BusinessLogo


class BusinessLogoSerializer(serializers.ModelSerializer):
    business = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = BusinessLogo


class BusinessSerializer(serializers.ModelSerializer):
    industry = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = Business
        fields = ["ticker", "name", "industry"]


class BusinessIndustrySerializer(serializers.ModelSerializer):
    businesses = BusinessSerializer(many=True)

    class Meta:
        model = BusinessIndustry
        fields = ["id", "name", "businesses"]

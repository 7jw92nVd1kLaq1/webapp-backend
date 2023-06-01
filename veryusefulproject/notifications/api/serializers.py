from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models import EntityType, Notification, NotificationAction, NotificationObject

User = get_user_model()


class NotificationActionSerializer(serializers.ModelSerializer):
    entity_type = serializers.SlugRelatedField(slug_field="entity_name")

    class Meta:
        model = NotificationAction


class NotificationObjectSerializer(serializers.ModelSerializer):
    action = NotificationActionSerializer()

    class Meta:
        model = NotificationObject


class NotificationSerializer(serializers.ModelSerializer):
    notification_object = NotificationObjectSerializer()

    class Meta:
        model = Notification
        exclude = ['actor']

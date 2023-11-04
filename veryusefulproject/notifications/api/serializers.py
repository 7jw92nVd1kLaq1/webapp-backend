from django.contrib.auth import get_user_model
from rest_framework import serializers

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin

from ..models import EntityType, Notification, NotificationAction, NotificationObject, NotificationObjectActor, NotificationObjectAffectedEntity, NotificationObjectInvolvedEntity

User = get_user_model()


class NotificationActionSerializer(DynamicFieldsSerializerMixin ,serializers.ModelSerializer):
    entity_type = serializers.SlugRelatedField(slug_field="entity_name")

    class Meta:
        model = NotificationAction


class NotificationObjectSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    action = NotificationActionSerializer()

    class Meta:
        model = NotificationObject


class NotificationObjectActorSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NotificationObjectActor


class NotificationObjectAffectedEntitySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NotificationObjectAffectedEntity


class NotificationObjectInvolvedEntitySerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NotificationObjectInvolvedEntity


class NotificationSerializer(DynamicFieldsSerializerMixin ,serializers.ModelSerializer):
    notification_object = NotificationObjectSerializer()

    class Meta:
        model = Notification

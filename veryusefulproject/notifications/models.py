from django.contrib.auth import get_user_model
from django.db import models

from uuid import uuid4

from .utils import stringify_notification

from veryusefulproject.core.models import BaseModel


User = get_user_model()


class EntityType(BaseModel):
    entity_name = models.CharField(max_length=128)


class NotificationAction(BaseModel):
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    action = models.CharField(max_length=256)
    code = models.CharField(max_length=128)
    desc = models.CharField(max_length=256)

    class Meta:
        unique_together = ['entity_type', 'action']


class NotificationObject(BaseModel):
    action = models.ForeignKey(NotificationAction, on_delete=models.RESTRICT)
    
    def __str__(self):
        return "NotificationObject: {}".format(self.id)

    def stringify(self):
        return stringify_notification(self)


class NotificationObjectActor(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']


class NotificationObjectAffectedEntity(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']


class NotificationObjectInvolvedEntity(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']


class Notification(BaseModel):
    identifier = models.UUIDField(default=uuid4)
    notifiers = models.ManyToManyField(
        User, 
        related_name="notification_as_notifiers"
    )
    notification_object = models.ForeignKey(
        NotificationObject, 
        on_delete=models.RESTRICT
    )
    read = models.BooleanField(default=False)

    def __str__(self):
        return "Notification: {}".format(self.id)

    def get_notifiers(self):
        return self.notifiers.all()

    def add_notifier(self, user):
        self.notifiers.add(user)

    def remove_notifier(self, user):
        self.notifiers.remove(user)

    def get_actor(self):
        return self.actor



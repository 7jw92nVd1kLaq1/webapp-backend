from django.contrib.auth import get_user_model
from django.db import models


from veryusefulproject.core.models import BaseModel
# Create your models here.

User = get_user_model()


class EntityType(BaseModel):
    entity_name = models.CharField(max_length=128)
    desc = models.TextField()


class NotificationAction(BaseModel):
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    action = models.CharField(max_length=256)
    desc = models.TextField()

    class Meta:
        unique_together = ['entity_type', 'action']


class NotificationObject(BaseModel):
    action = models.ForeignKey(NotificationAction, on_delete=models.RESTRICT)
    entity_id = models.TextField()


class Notification(BaseModel):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_actor")
    notifiers = models.ManyToManyField(User, related_name="notification_notifiers")
    notification_object = models.ForeignKey(NotificationObject, on_delete=models.RESTRICT)

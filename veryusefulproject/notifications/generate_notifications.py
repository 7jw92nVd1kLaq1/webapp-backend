from .models import Notification, NotificationObjectActor, NotificationObjectAffectedEntity, NotificationObjectInvolvedEntity, NotificationAction, NotificationObject, User, EntityType
from veryusefulproject.orders.models import Order


# Utility functions for creating a notification in response to events on behalf of other functions
def create_notification_for_successful_order_creation(order, user):
    if type(order) != Order:
        raise Exception("Invalid order object.")
    if type(user) != User:
        raise Exception("Invalid user object.")

    action = NotificationAction.objects.get(code="order:created")
    notification_object = NotificationObject.objects.create(action=action)
    NotificationObjectAffectedEntity.objects.create(
        notification_object=notification_object,
        entity_type=EntityType.objects.get(entity_name="Order"),
        entity_id=order.id
    )
    notification = Notification.objects.create(
        notification_object=notification_object
    )
    notification.notifiers.add(user)

    return notification

from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from veryusefulproject.core.mixins import PaginationHandlerMixin
from veryusefulproject.users.api.authentication import JWTAuthentication

from ..paginations import NotificationPagination
from ..models import Notification


class MarkNotificationAsReadView(UpdateAPIView):
    def update(self, request, *args, **kwargs):
        if request.method != "PATCH":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        notification_identifier = request.data.get("id", None)

        if not notification_identifier:
            number_of_notifications_updated = Notification.objects.filter(
                notifiers__username=request.user.get_username()
            ).update(read=True)

            return Response(
                status=status.HTTP_200_OK,
                data={"message": number_of_notifications_updated}
            )
        
        with transaction.atomic():
            try:
                notification = Notification.objects.get(
                    notifiers__username=request.user.get_username(), 
                    identifier=notification_identifier
                )
                notification.read = True
                notification.save()
                return Response(status=status.HTTP_200_OK)
            except Notification.DoesNotExist:
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"reason": "Notification not found."}
                )
            except:
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    data={"reason": "An unknown error occurred."}
                )


class RetrieveAllNotificationsView(PaginationHandlerMixin, RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)
    pagination_class = NotificationPagination

    def retrieve(self, request, *args, **kwargs):
        """
        Returns a paginated list of notifications whose content includes, but is not 
        limited to, their uuid, notification, and the action code that triggered the 
        notification.
        """

        defer = [
            "notifiers",
            "modified_at",
            "notification_object__created_at",
            "notification_object__modified_at",
            "notification_object__action__created_at",
            "notification_object__action__modified_at",
        ]

        return_data = {"notifications": []}

        user = request.user
        notifications = Notification.objects.select_related(
            "notification_object__action"
        ).prefetch_related(
            "notificationobjectactor_set",
            "notificationobjectaffected_set",
            "notificationobjectinvolved_set",
        ).filter(
            notifiers__username=user.get_username()
        ).order_by('-created_at').defer(*defer)

        return_data["unread_total"] = Notification.objects.filter(
            notifiers__username=user.get_username(), 
            read=False
        ).count()

        page = self.paginate_queryset(notifications)
        if page is not None:
            for notification in page:
                return_data["notifications"].append(
                    {
                        "id": str(notification.identifier),
                        "notification": notification.notification_object.stringify(),
                        "action": notification.notification_object.action.code,
                        "created_at": notification.created_at,
                        "read": notification.read,
                    }
                )

            return self.get_paginated_response(return_data)

        return Response(data=return_data, status=status.HTTP_200_OK)

        
class RetrieveNotificationsView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns a list of notifications whose content includes their uuid, notification,
        and the action code that triggered the notification.
        """

        defer = [
            "notifiers",
            "modified_at",
            "notification_object__created_at",
            "notification_object__modified_at",
            "notification_object__action__created_at",
            "notification_object__action__modified_at",
        ]

        return_data = {"notifications": []}

        user = request.user
        notifications = Notification.objects.select_related(
            "notification_object__action"
        ).prefetch_related(
            "notificationobjectactor_set",
            "notificationobjectaffected_set",
            "notificationobjectinvolved_set",
        ).filter(
            notifiers__username=user.get_username()
        ).order_by('-created_at').defer(*defer)

        return_data["total"] = Notification.objects.filter(
            notifiers__username=user.get_username()
        ).count()
        return_data["unread_total"] = Notification.objects.filter(
            notifiers__username=user.get_username(), read=False
        ).count()

        for notification in notifications:
            return_data["notifications"].append(
                {
                    "id": str(notification.identifier),
                    "notification": notification.notification_object.stringify(),
                    "action": notification.notification_object.action.code,
                    "created_at": notification.created_at,
                    "read": notification.read,
                }
            )

            if len(return_data) == 3:
                break

        return Response(data=return_data, status=status.HTTP_200_OK)

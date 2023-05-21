from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.notifications'

    def ready(self):
        try:
            import veryusefulproject.notifications.signals
        except ImportError:
            pass

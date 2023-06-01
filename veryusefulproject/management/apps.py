from django.apps import AppConfig


class ManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "veryusefulproject.management"

    def ready(self):
        try:
            import veryusefulproject.management.signals
        except:
            pass

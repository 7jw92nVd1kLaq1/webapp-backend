from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.core'

    def ready(self):
        try:
            import veryusefulproject.core.signals
        except:
            pass

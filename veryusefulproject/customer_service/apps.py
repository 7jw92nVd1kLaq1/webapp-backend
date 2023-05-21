from django.apps import AppConfig


class CustomerServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.customer_service'

    def ready(self):
        try:
            import veryusefulproject.customer_service.signals
        except:
            pass

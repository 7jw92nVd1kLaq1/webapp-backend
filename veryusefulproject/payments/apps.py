from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.payments'

    def ready(self):
        try:
            import veryusefulproject.payments.signals
        except:
            pass

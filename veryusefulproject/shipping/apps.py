from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.shipping'

    def ready(self):
        try:
            import veryusefulproject.shipping.signals
        except:
            pass

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.orders'

    def ready(self):
        try:
            import veryusefulproject.orders.signals
        except:
            pass

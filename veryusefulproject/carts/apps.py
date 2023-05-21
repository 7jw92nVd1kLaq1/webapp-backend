from django.apps import AppConfig


class CartsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.carts'

    def ready(self):
        try:
            import veryusefulproject.carts.signals
        except:
            pass

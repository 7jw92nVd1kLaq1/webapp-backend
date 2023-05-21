from django.apps import AppConfig


class RequestMarketplaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.request_marketplace'

    def ready(self):
        try:
            import veryusefulproject.request_marketplace.signals
        except:
            pass

from django.apps import AppConfig


class OfferMarketplaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.offer_marketplace'

    def ready(self):
        try:
            import veryusefulproject.offer_marketplace.signals
        except:
            pass

from django.apps import AppConfig


class CurrenciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.currencies'

    def ready(self):
        try:
            import veryusefulproject.currencies.signals
        except:
            pass

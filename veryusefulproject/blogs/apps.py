from django.apps import AppConfig


class BlogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veryusefulproject.blogs'

    def ready(self):
        try:
            import veryusefulproject.blogs.signals
        except:
            pass

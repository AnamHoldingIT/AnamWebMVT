from django.apps import AppConfig


class ZlinkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zlink'

    def ready(self):
        import zlink.signals

from django.apps import AppConfig


class PurchaseReturnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'purchase_return'

    def ready(self):
        import purchase_return.signals
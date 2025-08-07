from django.apps import AppConfig


class SalesReturnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_return'
    
    def ready(self):
        import sales_return.signals
from .customer_urls import urlpatterns as customer_urls
from .supplier_urls import urlpatterns as supplier_urls

urlpatterns = [
    *customer_urls,
    *supplier_urls,
]
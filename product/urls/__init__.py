from .product import urlpatterns as product_patterns
from .unit import urlpatterns as unit_patterns
from .brand import urlpatterns as brand_patterns
from .productcategory import urlpatterns as category_patterns

urlpatterns = [
    *product_patterns,
    *unit_patterns,
    *brand_patterns,
    *category_patterns,
]
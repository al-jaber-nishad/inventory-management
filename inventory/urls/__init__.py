from django.urls import path
from .stock_report import urlpatterns as stock_report_patterns
from .adjustment import urlpatterns as adjustment_patterns
from inventory.views.dashboard import dashboard_view

urlpatterns = [
    path('dashboard/', dashboard_view, name='inventory_dashboard'),
    *stock_report_patterns,
    *adjustment_patterns,
]
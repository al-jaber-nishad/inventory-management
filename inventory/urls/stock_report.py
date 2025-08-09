from django.urls import path
from inventory.views.stock_report import stock_report

urlpatterns = [
    path('stock-report/', stock_report, name='stock_report_list'),
]
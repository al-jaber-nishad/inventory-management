from django.urls import path
from sales.views import sales as views

urlpatterns = [
    path('sales/', views.SaleListView.as_view(), name='sale_list'),
    path('sales/<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('sales/create/', views.SaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:pk>/update/', views.SaleUpdateView.as_view(), name='sale_update'),
    path('sales/<int:pk>/delete/', views.SaleDeleteView.as_view(), name='sale_delete'),
    path('sales/<int:pk>/invoice/', views.sale_invoice_pdf, name='sale_invoice_pdf'),
]
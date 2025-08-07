from django.urls import path
from sales_return.views import sales_return as views

urlpatterns = [
    path('sale-returns/', views.SaleReturnListView.as_view(), name='sale_return_list'),
    path('sale-returns/<int:pk>/', views.SaleReturnDetailView.as_view(), name='sale_return_detail'),
    path('sale-returns/create/', views.SaleReturnCreateView.as_view(), name='sale_return_create'),
    path('sale-returns/<int:pk>/update/', views.SaleReturnUpdateView.as_view(), name='sale_return_update'),
    path('sale-returns/<int:pk>/delete/', views.SaleReturnDeleteView.as_view(), name='sale_return_delete'),
    path('sale-returns/<int:pk>/invoice/', views.sale_return_invoice_pdf, name='sale_return_invoice_pdf'),
]
from django.urls import path
from purchase_return.views import purchase_return as views

urlpatterns = [
    path('purchase-returns/', views.PurchaseReturnListView.as_view(), name='purchase_return_list'),
    path('purchase-returns/<int:pk>/', views.PurchaseReturnDetailView.as_view(), name='purchase_return_detail'),
    path('purchase-returns/create/', views.PurchaseReturnCreateView.as_view(), name='purchase_return_create'),
    path('purchase-returns/<int:pk>/update/', views.PurchaseReturnUpdateView.as_view(), name='purchase_return_update'),
    path('purchase-returns/<int:pk>/delete/', views.PurchaseReturnDeleteView.as_view(), name='purchase_return_delete'),
    path('purchase-returns/<int:pk>/invoice/', views.purchase_return_invoice_pdf, name='purchase_return_invoice_pdf'),
]
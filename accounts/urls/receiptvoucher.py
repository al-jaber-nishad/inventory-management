from django.urls import path
from accounts.views import receiptvoucher as views

urlpatterns = [
    path('receipt-vouchers/', views.ReceiptVoucherListView.as_view(), name='receiptvoucher_list'),
    path('receipt-vouchers/create/', views.ReceiptVoucherCreateView.as_view(), name='receiptvoucher_create'),
    path('receipt-vouchers/<int:pk>/', views.ReceiptVoucherDetailView.as_view(), name='receiptvoucher_detail'),
    path('receipt-vouchers/<int:pk>/update/', views.ReceiptVoucherUpdateView.as_view(), name='receiptvoucher_update'),
    path('receipt-vouchers/<int:pk>/delete/', views.ReceiptVoucherDeleteView.as_view(), name='receiptvoucher_delete'),
]
from django.urls import path
from accounts.views import paymentvoucher as views

urlpatterns = [
    path('payment-vouchers/', views.PaymentVoucherListView.as_view(), name='paymentvoucher_list'),
    path('payment-vouchers/create/', views.PaymentVoucherCreateView.as_view(), name='paymentvoucher_create'),
    path('payment-vouchers/<int:pk>/', views.PaymentVoucherDetailView.as_view(), name='paymentvoucher_detail'),
    path('payment-vouchers/<int:pk>/update/', views.PaymentVoucherUpdateView.as_view(), name='paymentvoucher_update'),
    path('payment-vouchers/<int:pk>/delete/', views.PaymentVoucherDeleteView.as_view(), name='paymentvoucher_delete'),
]
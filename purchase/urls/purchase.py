from django.urls import path
from purchase.views import purchase as views

urlpatterns = [
    path('purchases/', views.PurchaseListView.as_view(), name='purchase_list'),
    path('purchases/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase_detail'),
    path('purchases/create/', views.PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/update/', views.PurchaseUpdateView.as_view(), name='purchase_update'),
    path('purchases/<int:pk>/delete/', views.PurchaseDeleteView.as_view(), name='purchase_delete'),
]
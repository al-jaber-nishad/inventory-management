from django.urls import path
from inventory.views import adjustment as views

urlpatterns = [
    path('adjustments/', views.AdjustmentListView.as_view(), name='adjustment_list'),
    path('adjustments/<int:pk>/', views.AdjustmentDetailView.as_view(), name='adjustment_detail'),
    path('adjustments/create/', views.AdjustmentCreateView.as_view(), name='adjustment_create'),
    path('adjustments/<int:pk>/update/', views.AdjustmentUpdateView.as_view(), name='adjustment_update'),
    path('adjustments/<int:pk>/delete/', views.AdjustmentDeleteView.as_view(), name='adjustment_delete'),
]
from django.urls import path
from product.views import unit as views

urlpatterns = [
    path('units/', views.UnitListView.as_view(), name='unit_list'),
    path('units/create/', views.UnitCreateView.as_view(), name='unit_create'),
    path('units/create-ajax/', views.create_unit_ajax, name='unit_create_ajax'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit_detail'),
    path('units/<int:pk>/update/', views.UnitUpdateView.as_view(), name='unit_update'),
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='unit_delete'),
]

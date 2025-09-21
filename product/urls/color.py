from django.urls import path
from product.views import color as views

urlpatterns = [
    path('colors/', views.ColorListView.as_view(), name='color_list'),
    path('colors/create/', views.ColorCreateView.as_view(), name='color_create'),
    path('colors/create-ajax/', views.create_color_ajax, name='color_create_ajax'),
    path('colors/<int:pk>/', views.ColorDetailView.as_view(), name='color_detail'),
    path('colors/<int:pk>/update/', views.ColorUpdateView.as_view(), name='color_update'),
    path('colors/<int:pk>/delete/', views.ColorDeleteView.as_view(), name='color_delete'),
]
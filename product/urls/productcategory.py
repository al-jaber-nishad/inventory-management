from django.urls import path
from product.views import productcategory as views

urlpatterns = [
    path('categories/', views.ProductCategoryListView.as_view(), name='productcategory_list'),
    path('categories/create/', views.ProductCategoryCreateView.as_view(), name='productcategory_create'),
    path('categories/<int:pk>/', views.ProductCategoryDetailView.as_view(), name='productcategory_detail'),
    path('categories/<int:pk>/update/', views.ProductCategoryUpdateView.as_view(), name='productcategory_update'),
    path('categories/<int:pk>/delete/', views.ProductCategoryDeleteView.as_view(), name='productcategory_delete'),
]

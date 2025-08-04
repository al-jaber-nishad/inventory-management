# urls.py
from django.urls import path
from sms.views import assigned_package_views as views

urlpatterns = [
    path('assigned_package_list/', views.assigned_package_list, name='assigned_package_list'),

    path('assigned_package_create/', views.assigned_package_create, name='assigned_package_create'),

    path('assigned_package_update/<int:pk>/', views.assigned_package_update, name='assigned_package_update'),
    
    path('assigned_package_delete/<int:pk>/', views.assigned_package_delete, name='assigned_package_delete'),
]

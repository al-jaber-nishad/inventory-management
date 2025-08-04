from django.urls import path
from sms.views import assigned_sms_api_views as views

urlpatterns = [
    path('assigned_message_api_list', views.assigned_sms_api_list, name='assigned_sms_api_list'),

    path('assigned_message_api_create', views.assigned_sms_api_create, name='assigned_sms_api_create'),

    path('assigned_message_api_update/<int:pk>/', views.assigned_sms_api_update, name='assigned_sms_api_update'),
    
    path('assigned_message_api_delete/<int:pk>/', views.assigned_sms_api_delete, name='assigned_sms_api_delete'),


    # path('assign-api/', views.assign_sms_api, name='assign_sms_api'),
    
    # path('update-priority/', views.update_priority, name='update_priority'),
]

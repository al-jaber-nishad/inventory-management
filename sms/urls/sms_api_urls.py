
from django.urls import path
from sms.views import sms_api_views as views


urlpatterns = [
	path('message_api_list/', views.sms_api_list, name='sms_api_list'),

	path('message_api_create/', views.sms_api_create, name='sms_api_create'),

	path('message_api_update/<int:pk>', views.sms_api_update, name='sms_api_update'),

    path('message_api/delete/<int:pk>/', views.sms_api_delete, name='sms_api_delete'),

]
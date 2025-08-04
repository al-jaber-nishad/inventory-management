
from django.urls import path
from sms.views import package_views as views


urlpatterns = [
	path('package_list/', views.package_list, name='package_list'),

	path('package_create/', views.package_create, name='package_create'),

	path('package_update/<int:pk>', views.package_update, name='package_update'),

    path('package/delete/<int:pk>/', views.package_delete, name='package_delete'),

]
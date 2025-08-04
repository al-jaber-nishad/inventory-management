
from django.urls import path
from authentication.views import contact_group_views as views


urlpatterns = [
    path('contact_group_list/', views.contact_group_list, name='contact_group_list'),

	path('contact_group_create/', views.contact_group_create, name='contact_group_create'),

	path('contact_group_update/<int:pk>', views.contact_group_update, name='contact_group_update'),

    path('contact_group_delete/<int:pk>/', views.contact_group_delete, name='contact_group_delete'),

]

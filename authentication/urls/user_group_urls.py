from django.urls import path 
from authentication.views import user_group_views as views 


urlpatterns = [
    path('user_group_list/', views.user_group_list, name='user_group_list'),

	path('user_group_create/', views.user_group_create, name='user_group_create'),

	path('user_group_update/<int:pk>', views.user_group_update, name='user_group_update'),

    path('user_group/delete/<int:pk>/', views.user_group_delete, name='user_group_delete'),
]
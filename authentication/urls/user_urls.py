# from authentication.views import user_views as views
# from django.urls import path
# from django.contrib.auth import views as auth_views


# urlpatterns = [
    
# 	path('', views.home, name='home'),	
    
# 	path('login/', auth_views.LoginView.as_view(), name='login'),
  	
# 	path('logout/', auth_views.LogoutView.as_view(), name='logout'),

# 	path('profile/', views.profile, name='profile'),


# 	# path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

# # 	path('login/', views.LoginView, name='login'),

# # 	path('logout/', views.LogoutView, name='logout'),

# # 	path('register/', views.create_user, name='register'),

# # 	path('all/', views.getAllUser, name='authentication-user-all'),

# # 	path('without_pagination/all/', views.getAllUserWithoutPagination, name='authentication-user-all-wp'),

# # 	path('<int:pk>', views.getAUser),

# # 	path('me/', views.getMySelfUser),

# # 	path('search/', views.searchUser),

# # 	path('update/<int:pk>', views.updateUser),

# # 	path('delete/<int:pk>', views.deleteUser),

# # 	path('passwordchange/<int:pk>', views.userPasswordChange),
    
# 	path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    
# 	path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'), name='password_reset_confirm'),
    
# 	path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),


# ]

from django.urls import path 
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from authentication.views import user_views as views 

urlpatterns = [
	path('', views.home, name="home"),
	#   path('edit-profile/<int:pk>', views.edit_profile, name="edit-profile"),
	# path('login/', auth_views.LoginView.as_view(), name='login'),
	path('login/', views.LoginView, name='login'),
	path('logout/', views.LogoutView, name='logout'),

	# path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
	path('password_reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html'), name='password_reset'),

	# User management
  
	path('profile/', views.profile, name='profile'),

	path('user_list/', views.user_list, name='user_list'),

	path('reseller_user_list/', views.reseller_list, name='reseller_list'),

	path('client_user_list/', views.client_list, name='client_list'),

	path('user_create/', views.user_create, name='user_create'),

	path('user_update/<int:pk>', views.user_update, name='user_update'),

    path('user/delete/<int:pk>/', views.user_delete, name='user_delete'),

    path('users/<int:pk>/change-password/', views.user_change_password, name='user_change_password'),

    # path('user/user_change_balance/<int:pk>', views.user_change_balance, name='user_change_balance'),

    path('user_list/get_user_balance/<int:pk>', views.get_user_balance, name='get_user_balance'),

    path('transaction_report/', views.transaction_report, name='transaction_report'),

	path('developer_api/', views.developer_api, name='developer_api'),

	path('generate-api-key/', views.generate_api_key, name='generate_api_key'),
  
    path('regenerate-api-key/', views.regenerate_api_key, name='regenerate_api_key'),

	# path('api/sendsms/', views.send_sms_api, name='send_sms_api'),



]

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
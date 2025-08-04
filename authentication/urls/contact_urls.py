
from django.urls import path
from authentication.views import contact_views as views


urlpatterns = [
    path('contact_list/', views.contact_list, name='contact_list'),
    
    path('django_contact_list/', views.django_contact_list, name='django_contact_list'),

	path('contact_create/', views.contact_create, name='contact_create'),

	path('contact_update/<int:pk>', views.contact_update, name='contact_update'),

    path('contact_delete/<int:pk>', views.contact_delete, name='contact_delete'),

]

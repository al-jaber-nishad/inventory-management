from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication Module
    # path('', views.index),
	path('', include('authentication.urls.role_urls')),
	path('', include('authentication.urls.user_urls')),
	path('', include('authentication.urls.user_group_urls')),
	path('', include('authentication.urls.contact_urls')),
	path('', include('authentication.urls.contact_group_urls')),


	path('', include('sms.urls.assigned_package_urls')),
	path('', include('sms.urls.assigned_sms_api_urls')),
	path('', include('sms.urls.package_urls')),
	path('', include('sms.urls.sms_api_urls')),
	path('', include('sms.urls.sms_urls')),
	
	# Products
	# path('brand/', include('product.urls.brand_urls')),	
	# path('category/', include('product.urls.category_urls')),

]

# Silk URL
# urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
urlpatterns += static(settings.MEDIA_URL,
						document_root=settings.MEDIA_ROOT)
from django.urls import path, include

urlpatterns = [
    path('', include('purchase_return.urls.purchase_return')),
]
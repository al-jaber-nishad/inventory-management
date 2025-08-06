from django.urls import path
from accounts.views import bank as views

urlpatterns = [
    path('banks/', views.BankListView.as_view(), name='bank_list'),
    path('banks/create/', views.BankCreateView.as_view(), name='bank_create'),
    path('banks/<int:pk>/', views.BankDetailView.as_view(), name='bank_detail'),
    path('banks/<int:pk>/update/', views.BankUpdateView.as_view(), name='bank_update'),
    path('banks/<int:pk>/delete/', views.BankDeleteView.as_view(), name='bank_delete'),
]
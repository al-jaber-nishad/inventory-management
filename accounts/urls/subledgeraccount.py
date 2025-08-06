from django.urls import path
from accounts.views import subledgeraccount as views

urlpatterns = [
    path('subledgeraccounts/', views.SubLedgerAccountListView.as_view(), name='subledgeraccount_list'),
    path('subledgeraccounts/create/', views.SubLedgerAccountCreateView.as_view(), name='subledgeraccount_create'),
    path('subledgeraccounts/<int:pk>/', views.SubLedgerAccountDetailView.as_view(), name='subledgeraccount_detail'),
    path('subledgeraccounts/<int:pk>/update/', views.SubLedgerAccountUpdateView.as_view(), name='subledgeraccount_update'),
    path('subledgeraccounts/<int:pk>/delete/', views.SubLedgerAccountDeleteView.as_view(), name='subledgeraccount_delete'),
]
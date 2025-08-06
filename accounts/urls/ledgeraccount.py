from django.urls import path
from accounts.views import ledgeraccount as views

urlpatterns = [
    path('ledgeraccounts/', views.LedgerAccountListView.as_view(), name='ledgeraccount_list'),
    path('ledgeraccounts/create/', views.LedgerAccountCreateView.as_view(), name='ledgeraccount_create'),
    path('ledgeraccounts/<int:pk>/', views.LedgerAccountDetailView.as_view(), name='ledgeraccount_detail'),
    path('ledgeraccounts/<int:pk>/update/', views.LedgerAccountUpdateView.as_view(), name='ledgeraccount_update'),
    path('ledgeraccounts/<int:pk>/delete/', views.LedgerAccountDeleteView.as_view(), name='ledgeraccount_delete'),
]
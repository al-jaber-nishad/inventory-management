from django.urls import path
from accounts.views.balance_sheet import balance_sheet_report

urlpatterns = [
    path('balance-sheet/', balance_sheet_report, name='balance_sheet_list'),
]
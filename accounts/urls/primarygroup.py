from django.urls import path
from accounts.views import primarygroup as views

urlpatterns = [
    path('primarygroups/', views.PrimaryGroupListView.as_view(), name='primarygroup_list'),
    path('primarygroups/create/', views.PrimaryGroupCreateView.as_view(), name='primarygroup_create'),
    path('primarygroups/<int:pk>/', views.PrimaryGroupDetailView.as_view(), name='primarygroup_detail'),
    path('primarygroups/<int:pk>/update/', views.PrimaryGroupUpdateView.as_view(), name='primarygroup_update'),
    path('primarygroups/<int:pk>/delete/', views.PrimaryGroupDeleteView.as_view(), name='primarygroup_delete'),
]
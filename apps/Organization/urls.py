from django.urls import path
from . import views
from .views import (
    OrgCreateView,
    OrgDeleteView,
    OrgDetailView,
    OrgUpdateView,
    TeamDetailView,
    TeamCreateView,
    TeamDeleteView,
    TeamUpdateView
)

urlpatterns = [
    path('org/<int:pk>/', OrgDetailView.as_view(), name='org-detail'),
    path('org/new/', OrgCreateView.as_view(), name='org-create'),
    path('org/<int:pk>/update/', OrgUpdateView.as_view(), name='org-update'),
    path('org/<int:pk>/delete/', OrgDeleteView.as_view(), name='org-delete'),
    path('team/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('team/new/', TeamCreateView.as_view(), name='team-create'),
    path('team/<int:pk>/update/', TeamUpdateView.as_view(), name='team-update'),
    path('team/<int:pk>/delete/', TeamDeleteView.as_view(), name='team-delete'),
    # Assuming we have only one organization right now. Clicking on that Org
    # (either in side pane or nav bar) should take him to this view. - to be implemented
    path('org/context/', views.context, name='org_context'),
    path('teams/', views.teams_list, name='teams-list'),
]
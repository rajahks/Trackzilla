from django.urls import path
from . import views
from .views import (
    OrgCreateView,
    OrgDeleteView,
    OrgDetailView,
    OrgUpdateView,
    OrgJoinView,
    TeamDetailView,
    TeamCreateView,
    TeamDeleteView,
    TeamUpdateView
)

    # TODO: All these urls needs to be ORG specific. Revisit and revise the urls.

app_name = 'Org'

urlpatterns = [
    path('org/<int:pk>/', OrgDetailView.as_view(), name='org-detail'),
    path('org/new/', OrgCreateView.as_view(), name='org-create'),
    path('org/<int:pk>/update/', OrgUpdateView.as_view(), name='org-update'),
    path('org/<int:pk>/delete/', OrgDeleteView.as_view(), name='org-delete'),
    path('org/join/<int:pk>/<slug:OrgName>', OrgJoinView, name='org-join'),
    path('team/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('team/new/', TeamCreateView.as_view(), name='team-create'),
    path('team/<int:pk>/update/', TeamUpdateView.as_view(), name='team-update'),
    path('team/<int:pk>/delete/', TeamDeleteView.as_view(), name='team-delete'),
    path('teams/', views.teams_list, name='teams-list'),
]
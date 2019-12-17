from django.urls import path
from . import views
from .views import ackResource, denyResource
from .views import (
    ResourceDetailView,
    ResourceCreateView,
    ResourceUpdateView,
    ResourceDeleteView,
)

app_name = 'Resource'

urlpatterns = [
    path('<int:pk>/', ResourceDetailView.as_view(), name='resource-detail'),
    path('new/', ResourceCreateView.as_view(), name='resource-create'),
    path('<int:pk>/update/', ResourceUpdateView.as_view(), name='resource-update'),
    path('<int:pk>/delete/', ResourceDeleteView.as_view(), name='resource-delete'),
    path('<int:pk>/acknowledge', ackResource, name='acknowledge_resource'),
    path('<int:pk>/deny', denyResource, name='deny_resource'),
    path('list/', views.resources_list, name='resources-list'),
]


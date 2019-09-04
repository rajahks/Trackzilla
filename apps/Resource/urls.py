from django.urls import path
from .views import (
    ResourceDetailView,
    ResourceCreateView,
    ResourceUpdateView,
    ResourceDeleteView,
)


urlpatterns = [
    path('resource/<int:pk>/', ResourceDetailView.as_view(), name='resource-detail'),
    path('resource/new/', ResourceCreateView.as_view(), name='resource-create'),
    path('resource/<int:pk>/update/', ResourceUpdateView.as_view(), name='resource-update'),
    path('resource/<int:pk>/delete/', ResourceDeleteView.as_view(), name='resource-delete'),
]
from django.urls import path, include
from .views import ackResource, denyResource

urlpatterns = [
    path('<int:pk>/acknowledge', ackResource, name='acknowledge_resource'),
    path('<int:pk>/deny', denyResource, name='deny_resource'),
]

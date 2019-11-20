from django.urls import path
from . import views
from .views import (
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserUpdateView,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('user/new/', UserCreateView.as_view(), name='user-create'),
    path('user/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
    path('people/', views.people_list, name='people-list')  #TODO: Hackfest Addition. Not sure why this was added. This maynot be required.
]
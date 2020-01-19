from django.urls import path
from . import views
from .views import (
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserUpdateView,
    ChangePasswordView,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    # path('user/new/', UserCreateView.as_view(), name='user-create'),  # TODO: Not exposing the create and update views for user as of now.
    # path('user/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
    path('user/<int:pk>/change-password', ChangePasswordView.as_view(), name='change-password'),
    # path('people/', views.people_list, name='people-list')  #TODO: Hackfest Addition. Not sure why this was added. This maynot be required.
]

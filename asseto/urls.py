from django.contrib import admin
from django.urls import path, include
from apps.Users import views as user_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='Users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='Users/logout.html'), name='logout'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('', include('apps.Users.urls')),
]

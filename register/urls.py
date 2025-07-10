from . import views
from django.contrib.auth import views as auth_views
from register.views import admin_login, admin_logout, register_superuser
from django.urls import path


urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('admin/login/', admin_login, name='admin_login'),
    path('admin-panel/logout/', admin_logout, name='admin_logout'),
    path('admin-panel/register-superuser/', register_superuser, name='register_superuser'),
]

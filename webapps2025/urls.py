from django.contrib import admin
from django.urls import path, include
from register.views import CustomLoginView
from payapp.views import home
from django.contrib.auth import views as auth_views
from register.views import admin_login
from payapp.views import mark_all_as_read

urlpatterns = [
    path('', home, name='home'),
    path('register/', include('register.urls')),
    path('payapp/', include('payapp.urls')),
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('admin-panel/login/', admin_login, name='admin_login'),
    path('admin-panel/login/', admin_login, name='admin_login'),
    path('mark_all_as_read/', mark_all_as_read, name='mark_all_as_read'),
]


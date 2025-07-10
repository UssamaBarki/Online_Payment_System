from django.urls import path
from . import views
from payapp.views import currency_conversion

urlpatterns = [
    path('direct_payment/', views.direct_payment, name='direct_payment'),
    path('request_payment/', views.create_payment_request, name='create_payment_request'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accept_request/<int:request_id>/', views.accept_payment_request, name='accept_payment_request'),
    path('reject_request/<int:request_id>/', views.reject_payment_request, name='reject_payment_request'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('convert/', views.convert_currency, name='convert_currency'),
    path('conversion/<str:currency1>/<str:currency2>/<str:amount>/', currency_conversion, name='currency_conversion'),
]

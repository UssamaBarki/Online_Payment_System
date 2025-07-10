from django.contrib import admin
from .models import Payment, PaymentRequest

admin.site.register(Payment)
admin.site.register(PaymentRequest)


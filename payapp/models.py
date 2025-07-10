from django.db import models
from django.contrib.auth.models import User
from thrift_client import get_timestamp

class Payment(models.Model):
    DIRECT_PAYMENT = 'direct'
    PAYMENT_REQUEST = 'request'
    ORIGIN_CHOICES = [
        (DIRECT_PAYMENT, 'Direct Payment'),
        (PAYMENT_REQUEST, 'Payment Request'),
    ]

    sender = models.ForeignKey(User, related_name='sent_payments', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_currency = models.CharField(max_length=3, default='GBP')
    timestamp = models.DateTimeField(default=get_timestamp)
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES, default=DIRECT_PAYMENT)
    read_status = models.BooleanField(default=False)
    def __str__(self):
        return f"Payment from {self.sender} to {self.recipient} of {self.amount} {self.currency}"


class PaymentRequest(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests')
    requestee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    timestamp = models.DateTimeField(default=get_timestamp)
    STATUS_CHOICES = [
         ('pending', 'Pending'),
         ('accepted', 'Accepted'),
         ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    read_status = models.BooleanField(default=False)
    def __str__(self):
        return f"Request from {self.requester.username} to {self.requestee.username}: {self.amount} {self.currency} ({self.status})"

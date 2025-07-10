from django.db import models
from django.contrib.auth.models import User


CURRENCY_CHOICES = (
    ('GBP', 'GB Pounds'),
    ('USD', 'US Dollars'),
    ('EUR', 'Euros'),
)

class OnlineAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.currency} Account"


User._meta.get_field('email')._unique = True


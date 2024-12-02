from django.contrib.auth.models import User
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(
        max_length=50, default="Cardholder", null=True, blank=True
    )
    last_name = models.CharField(max_length=50, default="Name", null=True, blank=True)
    is_employee = models.BooleanField(default=False)
    card_qr_code = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Customer Profile"

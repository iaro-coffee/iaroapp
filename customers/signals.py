from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile


@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, created, **kwargs):

    if created:
        CustomerProfile.objects.create(user=instance, is_employee=True)
    else:
        try:
            instance.customerprofile.save()
        except CustomerProfile.DoesNotExist:
            CustomerProfile.objects.create(user=instance, is_employee=True)

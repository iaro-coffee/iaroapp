from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import CustomerProfile
from users.models import Profile


@receiver(post_save, sender=CustomerProfile)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        return

    if instance.is_employee and not Profile.objects.filter(user=instance.user).exists():
        Profile.objects.create(user=instance.user)

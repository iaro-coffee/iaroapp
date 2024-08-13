from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import CustomerProfile
from employees.models import EmployeeProfile
from lib.pos_hello_tess import POSHelloTess, get_card_id_from_user


@receiver(post_save, sender=CustomerProfile)
def create_employee_profile(sender, instance, created, **kwargs):
    print(
        f"Function create_user_profile called with:\n sender={sender},"
        f"\n instance={instance},\n created={created},\n kwargs={kwargs}"
    )

    pos = POSHelloTess()
    request = pos.create_customer_card(get_card_id_from_user(instance.user))

    if not request:
        print("Error: Failed to create customer card.")
    else:
        print("Customer card created successfully.")

    if created:
        print("Instance was just created, exit function.")
        return

    if (
        instance.is_employee
        and not EmployeeProfile.objects.filter(user=instance.user).exists()
    ):
        print("Instance is an employee and profile does not exist.")
        EmployeeProfile.objects.create(user=instance.user)
        print("Profile created successfully for user.")
    else:
        print("No action needed, profile already exists.")

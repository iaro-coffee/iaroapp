from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import CustomerProfile
from employees.models import EmployeeProfile
from onboarding.models import Document


@receiver(post_save, sender=CustomerProfile)
def create_employee_profile(sender, instance, created, **kwargs):
    if created:
        return

    if (
        instance.is_employee
        and not EmployeeProfile.objects.filter(user=instance.user).exists()
    ):
        # Create EmployeeProfile if it does not exist
        employee_profile = EmployeeProfile.objects.create(user=instance.user)

        # Assign documents
        assign_documents_to_employee(employee_profile)


def assign_documents_to_employee(employee_profile):
    auto_assign_documents = Document.objects.filter(auto_assign_new_employees=True)

    for document in auto_assign_documents:
        document.assigned_employees.add(employee_profile)

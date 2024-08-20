from django.db.models.signals import post_save
from django.dispatch import receiver

from employees.models import EmployeeProfile
from onboarding.models import Document


@receiver(post_save, sender=EmployeeProfile)
def assign_documents_to_new_employee(sender, instance, created, **kwargs):
    if created:
        # Fetch all documents that should be auto-assigned
        auto_assign_documents = Document.objects.filter(auto_assign_new_employees=True)
        for document in auto_assign_documents:
            document.assigned_employees.add(instance)

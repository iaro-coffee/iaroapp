from django.contrib.auth.models import User
from django.db import models

from inventory.models import Branch


def get_first_branch_id():
    return Branch.objects.first().id


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(
        default="profile_avatars/avatar.png",  # default avatar
        upload_to="profile_avatars",  # dir to store the image
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=get_first_branch_id,
    )

    planday_id = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    onboarding_stages = models.JSONField(default=dict)
    # Use a string reference to avoid circular import
    personal_information_form = models.OneToOneField(
        "onboarding.PersonalInformation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )

    def __str__(self):
        return f"{self.user.username} Profile"

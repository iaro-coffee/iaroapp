from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from employees.models import EmployeeProfile
from inventory.models import Branch


class UserAdminCreationForm(UserCreationForm):
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True)

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "branch")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()
        EmployeeProfile.objects.create(user=user, branch=self.cleaned_data["branch"])
        return user

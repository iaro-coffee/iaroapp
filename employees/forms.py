from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from employees.models import EmployeeProfile
from inventory.models import Branch
from lib import planday

from .no_planday_email_exception import NoPlandayEmailException


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ["avatar", "branch"]


class UserClientCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    planday = planday.Planday()
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "branch")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        self.planday.authenticate()
        employees = self.planday.get_employees()
        for employee in employees.values():
            if user.email == employee["email"]:
                if commit:
                    user.save()
                    EmployeeProfile.objects.create(
                        user=user, branch=self.cleaned_data["branch"]
                    )
                return user, employee["employeeGroups"]
        raise NoPlandayEmailException("Email should correspond to your Planday Email.")
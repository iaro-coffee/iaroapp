from inventory.models import Branch
from .models import Profile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from lib import planday
from .no_planday_email_exception import NoPlandayEmailException


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'branch']


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    planday = planday.Planday()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        self.planday.authenticate()
        employees = self.planday.get_employees()
        for employee in employees.values():
            if user.email == employee["email"]:
                if commit:
                    user.save()
                return user, employee["employeeGroups"]
        raise NoPlandayEmailException


class UserCreationFormWithBranch(UserCreationForm):
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'branch')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()
        Profile.objects.create(user=user, branch=self.cleaned_data['branch'])
        return user

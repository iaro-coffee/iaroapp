from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from lib import planday
from registration.no_planday_email_exception import NoPlandayEmailException

# Create your forms here.


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    planday = planday.Planday()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        self.planday.authenticate()
        employees = self.planday.get_employees()
        for employee in employees.values():
            if user.email == employee["email"]:
                if commit:
                    user.save()
                return user, employee["employeeGroups"]
        raise NoPlandayEmailException

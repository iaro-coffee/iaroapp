from django import forms
from .models import CustomerProfile
from allauth.account.forms import LoginForm
from django import forms
from django.utils.translation import gettext_lazy as _


class CustomerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['first_name', 'last_name']


class CustomLoginForm(LoginForm):
    remember = forms.BooleanField(label=_("Remember Me"), required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['remember'].initial = True

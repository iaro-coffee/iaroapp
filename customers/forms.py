from .models import CustomerProfile
from allauth.account.forms import LoginForm, SignupForm
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
        self.fields['login'].label = _("Email")
        self.fields['login'].widget.attrs['placeholder'] = _("Email")
        self.fields['remember'].initial = True


class CustomSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = _("Email")
        self.fields.pop('username')
        self.fields['email'].label = _("Email")
        self.fields['email'].required = True
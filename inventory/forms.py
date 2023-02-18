from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import datetime  # for checking renewal date range.

from django import forms

from .models import Product

class Form(forms.ModelForm):
    class Meta:
        model = Product
        fields =('name','value')
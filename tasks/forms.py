from django.forms import ModelForm
from django import forms
from inventory.models import Product

class BakingPlanForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name']

    name = forms.CharField(required=False)
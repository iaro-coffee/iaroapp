from django.forms import ModelForm
from django import forms
from inventory.models import Product, Branch
from .models import BakingPlanInstance, Recipe

class BakingPlanForm(ModelForm):
    name = forms.CharField(required=False)
    value_ost = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control'}),required=False)
    value_west = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control'}),required=False)

    class Meta:
        model = Recipe
        fields = ['name', 'value_ost', 'value_west']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['value_ost'].widget = forms.TextInput(
            attrs={
                'name': f"{self.instance.id}_value_ost",
                'class': 'form-control',
                'pattern': '[0-9]+([.,][0-9]+)?',
                'inputmode': 'decimal'
            })
        self.fields['value_west'].widget = forms.TextInput(
            attrs={
                'name': f"{self.instance.id}_value_west",
                'class': 'form-control',
                'pattern': '[0-9]+([.,][0-9]+)?',
                'inputmode': 'decimal'
            })

from django import forms
from .models import Recipe, Product

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(seller__name='iaro bakery').order_by('name')

from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'

from django.forms import modelformset_factory

TaskFormset = modelformset_factory(
    Task,
    fields=('title', ),
    extra=1,
    widgets={'title': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Book title here'
        })
    }
)
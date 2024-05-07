from django import forms

from .models import Product

ProductFormset = forms.modelformset_factory(
    Product,
    fields=("name",),
    extra=1,
)

from .models import Product
from django import forms

ProductFormset = forms.modelformset_factory(
    Product,
    fields=('name', ),
    extra=1,
)
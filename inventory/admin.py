from django.contrib import admin

# Register your models here.

from .models import Product

class ProductsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Product

class ProductsAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name', 'value')

admin.site.register(Product, ProductsAdmin)
from django.contrib import admin

# Register your models here.

from .models import Product, Storage

class ProductsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Product

class ProductsAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name', 'value', 'value_intended', 'display_unit', 'display_category')
    readonly_fields = ("modified_date",)

admin.site.register(Product, ProductsAdmin)

class StoragesInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Storage

class StoragesAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name',)

admin.site.register(Storage, StoragesAdmin)
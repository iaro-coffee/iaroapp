from django.contrib import admin

# Register your models here.

from .models import Product, Storage, Seller, ProductStorage, Branch

class BranchesInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Branch

class BranchesAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name', 'display_storages', 'departmentId')

admin.site.register(Branch, BranchesAdmin)

class ProductStorageInline(admin.TabularInline):
   model = ProductStorage
   extra = 1

class ProductsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Product

class ProductsAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name', 'display_availability', 'display_unit', 'storages')
    readonly_fields = ("modified_date",)
    inlines = [ProductStorageInline]

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
    list_display = ('name', 'display_color')

admin.site.register(Storage, StoragesAdmin)

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('name',)
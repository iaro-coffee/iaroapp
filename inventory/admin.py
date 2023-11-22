from django.contrib import admin

# Register your models here.

from .models import Product, Storage, Category, Seller, ProductStorage

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
    list_display = ('name', 'display_availability', 'display_unit', 'display_category', 'storages')
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

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji', 'display_color')

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('name',)
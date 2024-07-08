from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Branch, Product, ProductStorage, Seller, Storage

# Register your models here.


class BranchesInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""

    model = Branch


@admin.register(Branch)
class BranchesAdmin(admin.ModelAdmin):
    """Administration object for Branch models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of branch instances in branch view (inlines)
    """

    list_display = ("name", "display_storages", "departmentId")


class ProductStorageInline(admin.TabularInline):
    model = ProductStorage
    readonly_fields = ("last_updated",)
    extra = 1


class ProductsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""

    model = Product


@admin.register(Product)
class ProductsAdmin(ImportExportModelAdmin):
    """Administration object for Product models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of product instances in product view (inlines)
    """

    list_display = ("name", "display_availability", "display_unit", "storages")
    readonly_fields = ("modified_date",)
    inlines = [ProductStorageInline]
    search_fields = ("name",)
    list_filter = (
        "product_storages__storage__branches",
        "product_storages__storage",
    )


class StoragesInline(admin.TabularInline):
    """Defines format of inline storage insertion (used in StorageAdmin)"""

    model = Storage


@admin.register(Storage)
class StoragesAdmin(admin.ModelAdmin):
    """Administration object for Storage models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of storage instances in storage view (inlines)
    """

    list_display = ("name", "display_color")


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    """Administration object for Seller models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds search fields and list filters (search_fields, list_filter)
    """

    list_display = ["name", "visibility", "is_weekly"]
    list_filter = ["visibility"]
    search_fields = ["name"]

from django.contrib import admin

# Register your models here.

from .models import Branch

class BranchesInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Branch

class BranchesAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('name', 'display_storages')

admin.site.register(Branch, BranchesAdmin)
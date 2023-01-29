from django.contrib import admin

# Register your models here.

from .models import Tip

class TipsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Tip

class TipsAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('user', 'note', 'date', 'amount')

admin.site.register(Tip, TipsAdmin)
from django.contrib import admin

# Register your models here.

from .models import Tips

"""Minimal registration of Models.
admin.site.register(Task)
admin.site.register(Author)
admin.site.register(TaskInstance)
admin.site.register(Weekdays)
"""

class TipsInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Tips


# class TipsAdmin(admin.ModelAdmin):
#     """Administration object for Task models.
#     Defines:
#      - fields to be displayed in list view (list_display)
#      - adds inline addition of task instances in task view (inlines)
#     """
#     list_display = ('title')


# admin.site.register(Tips, TipsAdmin)
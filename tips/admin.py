from django.contrib import admin

# Register your models here.

from .models import Tips #, TipsInstance

"""Minimal registration of Models.
admin.site.register(Task)
admin.site.register(Author)
admin.site.register(TaskInstance)
admin.site.register(Weekdays)
"""

# class TipsInline(admin.TabularInline):
#     """Defines format of inline task insertion (used in AuthorAdmin)"""
#     model = Tips

# class TipsInstanceInline(admin.TabularInline):
#     """Defines format of inline task instance insertion (used in TaskAdmin)"""
#     model = TipsInstance

# class TipsAdmin(admin.ModelAdmin):
#     """Administration object for Task models.
#     Defines:
#      - fields to be displayed in list view (list_display)
#      - adds inline addition of task instances in task view (inlines)
#     """
#     list_display = ('title')
#     inlines = [TipsInstanceInline]

# admin.site.register(Tips, TipsAdmin)
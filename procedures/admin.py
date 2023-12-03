from django.contrib import admin
from .models import Procedure, ProcedureCategory

class ProcedureAdmin(admin.ModelAdmin):
    """Administration object for Procedure models.
    Defines:
     - fields to be displayed in list view (list_display)
    """
    list_display = ('title', 'summary', 'category', 'display_branch')

admin.site.register(Procedure, ProcedureAdmin)
class ProcedureCategoryAdmin(admin.ModelAdmin):
    """Administration object for TaskInstance models.
    Defines:
     - fields to be displayed in list view (list_display)
     - filters that will be displayed in sidebar (list_filter)
     - grouping of fields into sections (fieldsets)
    """
    list_display = ('id', 'name')


admin.site.register(ProcedureCategory, ProcedureCategoryAdmin)
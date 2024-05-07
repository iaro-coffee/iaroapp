from django.contrib import admin

from .models import Procedure, ProcedureCategory


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    """Administration object for Procedure models.
    Defines:
     - fields to be displayed in list view (list_display)
    """

    list_display = ("title", "summary", "category", "display_branch")


@admin.register(ProcedureCategory)
class ProcedureCategoryAdmin(admin.ModelAdmin):
    """Administration object for TaskInstance models.
    Defines:
     - fields to be displayed in list view (list_display)
     - filters that will be displayed in sidebar (list_filter)
     - grouping of fields into sections (fieldsets)
    """

    list_display = ("id", "name")

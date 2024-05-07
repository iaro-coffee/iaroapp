from django.contrib import admin

from .models import Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Administration object for Shift models.
    Defines:
     - fields to be displayed in list view (list_display)
    """

    list_display = ("user", "start_date", "end_date", "rating")

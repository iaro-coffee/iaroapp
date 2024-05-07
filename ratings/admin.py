from django.contrib import admin

from .models import EmployeeRating


@admin.register(EmployeeRating)
class EmployeeRatingAdmin(admin.ModelAdmin):
    """Administration object for EmployeeRating models.
    Defines:
     - fields to be displayed in list view (list_display)
    """

    list_display = ("id", "user", "date", "rating")

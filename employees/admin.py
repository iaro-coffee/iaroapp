from django.contrib import admin

from employees.models import EmployeeProfile


@admin.register(EmployeeProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "avatar")
    search_fields = (
        "user__username__icontains",
        "user__email__icontains",
        "branch__name__icontains",
    )
    ordering = ("user__username",)

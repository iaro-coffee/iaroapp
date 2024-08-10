from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from customers.models import CustomerProfile
from employees.models import EmployeeProfile

from .forms import UserAdminCreationForm


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = "Profiles"
    fk_name = "user"


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = "Profiles"
    fk_name = "user"
    readonly_fields = ("card_qr_code",)


class CustomUserAdmin(BaseUserAdmin):
    add_form = UserAdminCreationForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "branch"),
            },
        ),
    )
    inlines = (
        EmployeeProfileInline,
        CustomerProfileInline,
    )
    search_fields = ("username", "email")

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

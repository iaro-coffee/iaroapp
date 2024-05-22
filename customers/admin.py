from django.contrib import admin
from .models import CustomerProfile


class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'is_employee')
    search_fields = ('user__username__icontains', 'user__email__icontains', 'first_name__icontains', 'last_name__icontains')


admin.site.register(CustomerProfile, CustomerProfileAdmin)

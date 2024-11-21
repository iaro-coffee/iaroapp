from typing import List, Tuple

from django.contrib import admin

from employees.models import EmployeeProfile

from .models import Document, PersonalInformation, SignedDocument


@admin.register(PersonalInformation)
class PersonalInformationAdmin(admin.ModelAdmin):
    list_display: List[str] = ["last_name", "first_name", "date_submitted"]
    search_fields: List[str] = ["last_name", "first_name", "tax_id"]
    ordering: Tuple[str, ...] = ("-date_submitted",)

    fieldsets: List[Tuple[str, dict]] = [
        (
            None,
            {
                "fields": [
                    "last_name",
                    "first_name",
                    "street",
                    "city_zip",
                    "city_name",
                    "birth_date",
                    "gender_check",
                    "insurance_number",
                    "birth_place",
                    "disability_check",
                ]
            },
        ),
        (
            "Occupation Details",
            {
                "fields": [
                    "job_title",
                    "emp_type_check",
                    "additional_employment_check",
                    "minor_employment_check",
                    "highest_edu_check",
                    "highest_training_check",
                    "weekly_hours_check",
                ]
            },
        ),
        (
            "Tax and Social Insurance",
            {"fields": ["tax_id", "health_insurance", "health_insurance_number"]},
        ),
    ]

    readonly_fields = ["date_submitted"]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append("date_submitted")
        return readonly


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "template_id", "auto_assign_new_employees")
    search_fields = ("name", "description", "template_id")
    # filter_horizontal = ("assigned_employees",)
    readonly_fields = ("assigned_employees",)

    def save_model(self, request, obj, form, change):
        # Automatically assign the document to all employees if the option is enabled
        super().save_model(request, obj, form, change)
        if obj.auto_assign_new_employees:
            all_employees = EmployeeProfile.objects.all()
            obj.assigned_employees.add(*all_employees)


@admin.register(SignedDocument)
class SignedDocumentAdmin(admin.ModelAdmin):
    list_display = ("document", "user_full_name", "signed_at", "signing_status")
    search_fields = [
        "user__employeeprofile__first_name",
        "user__employeeprofile__last_name",
        "document__name",
        "request_id",
        "action_id",
    ]
    readonly_fields = [
        "user",
        "user_full_name",
        "document",
        "signing_url",
        "request_id",
        "action_id",
        "signing_status",
        "signed_at",
    ]

    @admin.display(description="Full Name")
    def user_full_name(self, obj):
        return obj.user_full_name()

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

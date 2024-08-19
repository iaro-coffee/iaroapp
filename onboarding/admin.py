from typing import List, Tuple

from django.contrib import admin
from django.db import models

from .models import Document, PersonalInformation, SignedDocument


@admin.register(PersonalInformation)
class PersonalInformationAdmin(admin.ModelAdmin):
    list_display: List[str] = ["familienname", "vorname", "date_submitted"]
    search_fields: List[str] = ["familienname", "vorname", "steuer_id"]
    ordering: Tuple[str, ...] = ("-date_submitted",)

    fieldsets: List[Tuple[str, models.fields]] = [
        (
            None,
            {
                "fields": [
                    "familienname",
                    "vorname",
                    "strasse_hausnummer",
                    "plz_ort",
                    "geburtsdatum",
                    "geschlecht",
                    "versicherungsnummer",
                    "geburtsort_land",
                    "schwerbehindert",
                ]
            },
        ),
        (
            "Occupation Details",
            {
                "fields": [
                    "berufsbezeichnung",
                    "ausgeubte_tatigkeit",
                    "beschaftigungsart",
                    "weitere_beschaftigung",
                    "geringfugige_beschaftigung",
                    "hochster_schulabschluss",
                    "hochste_berufsausbildung",
                    "wochentliche_arbeitszeit",
                ]
            },
        ),
        (
            "Tax and Social Insurance",
            {"fields": ["steuer_id", "gesetzliche_krankenkasse"]},
        ),
        (
            "Submission Details",
            {"fields": ["date_submitted", "unterschrift_arbeitnehmer"]},
        ),
    ]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "template_id")
    search_fields = ("name", "description", "template_id")


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

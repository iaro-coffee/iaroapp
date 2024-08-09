from typing import List, Tuple

from django.contrib import admin
from django.db import models

from onboarding.models import PersonalInformation


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


# Register the model with the enhanced admin class

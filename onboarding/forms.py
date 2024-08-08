from django import forms

from .models import PersonalInformation


class PersonalInformationForm(forms.ModelForm):
    consent = forms.BooleanField(
        label="I agree to allow Iaro Cafe to process my personal information",
        required=True,
        error_messages={"required": "You must agree to the terms to proceed."},
    )

    class Meta:
        model = PersonalInformation
        fields = [
            "familienname",
            "vorname",
            "strasse_hausnummer",
            "plz_ort",
            "geburtsdatum",
            "geschlecht",
            "versicherungsnummer",
            "geburtsort_land",
            "schwerbehindert",
            "iban",
            "bic",
            "berufsbezeichnung",
            "ausgeubte_tatigkeit",
            "beschaftigungsart",
            "weitere_beschaftigung",
            "geringfugige_beschaftigung",
            "hochster_schulabschluss",
            "hochste_berufsausbildung",
            "wochentliche_arbeitszeit",
            "steuer_id",
            "gesetzliche_krankenkasse",
            "unterschrift_arbeitnehmer",
            "consent",
        ]

        widgets = {
            "familienname": forms.TextInput(
                attrs={"placeholder": "Familienname", "class": "form-control"}
            ),
            "vorname": forms.TextInput(
                attrs={"placeholder": "Vorname", "class": "form-control"}
            ),
            "strasse_hausnummer": forms.TextInput(
                attrs={
                    "placeholder": "Straße und Hausnummer inkl. Anschriftenzusatz",
                    "class": "form-control",
                }
            ),
            "plz_ort": forms.TextInput(
                attrs={"placeholder": "PLZ, Ort", "class": "form-control"}
            ),
            "geburtsdatum": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "geschlecht": forms.RadioSelect(choices=PersonalInformation.GENDER_CHOICES),
            "versicherungsnummer": forms.TextInput(
                attrs={
                    "placeholder": "Versicherungsnummer, gem. Sozialvers. Ausweis",
                    "class": "form-control",
                }
            ),
            "geburtsort_land": forms.TextInput(
                attrs={"placeholder": "Geburtsort, -land", "class": "form-control"}
            ),
            "schwerbehindert": forms.RadioSelect(
                choices=PersonalInformation.DISABILITY_CHOICES
            ),
            "iban": forms.TextInput(
                attrs={"placeholder": "IBAN", "class": "form-control"}
            ),
            "bic": forms.TextInput(
                attrs={"placeholder": "BIC", "class": "form-control"}
            ),
            "berufsbezeichnung": forms.TextInput(
                attrs={"placeholder": "Berufsbezeichnung", "class": "form-control"}
            ),
            "ausgeubte_tatigkeit": forms.TextInput(
                attrs={"placeholder": "Ausgeübte Tätigkeit", "class": "form-control"}
            ),
            "beschaftigungsart": forms.RadioSelect(
                choices=PersonalInformation.EMPLOYMENT_TYPE_CHOICES
            ),
            "weitere_beschaftigung": forms.RadioSelect(
                choices=PersonalInformation.ADDITIONAL_EMPLOYMENT_CHOICES
            ),
            "geringfugige_beschaftigung": forms.RadioSelect(
                choices=PersonalInformation.MINOR_EMPLOYMENT_CHOICES
            ),
            "hochster_schulabschluss": forms.RadioSelect(
                choices=PersonalInformation.EDUCATION_CHOICES
            ),
            "hochste_berufsausbildung": forms.RadioSelect(
                choices=PersonalInformation.TRAINING_CHOICES
            ),
            "wochentliche_arbeitszeit": forms.RadioSelect(
                choices=PersonalInformation.WORK_HOURS_CHOICES
            ),
            "steuer_id": forms.TextInput(
                attrs={
                    "placeholder": "Steuer Identifikationsnr.",
                    "class": "form-control",
                }
            ),
            "gesetzliche_krankenkasse": forms.TextInput(
                attrs={
                    "placeholder": "Gesetzliche Krankenkasse",
                    "class": "form-control",
                }
            ),
            "unterschrift_arbeitnehmer": forms.TextInput(
                attrs={
                    "placeholder": "Unterschrift Arbeitnehmer",
                    "class": "form-control",
                }
            ),
        }

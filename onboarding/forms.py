from django import forms
from django.utils.translation import gettext_lazy as _

from .models import PersonalInformation


class PersonalInformationForm(forms.ModelForm):
    consent = forms.BooleanField(
        label=_("I agree to allow Iaro Cafe to process my personal information"),
        required=True,
        error_messages={"required": _("You must agree to the terms to proceed.")},
    )

    class Meta:
        model = PersonalInformation
        fields = [
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
            "nationality",
            "iban",
            "bic",
            "job_title",
            "emp_type_check",
            "additional_employment_check",
            "minor_employment_check",
            "highest_edu_check",
            "highest_training_check",
            "weekly_hours_check",
            "tax_id",
            "health_insurance",
            "health_insurance_number",
        ]
        labels = {
            "last_name": _("Last Name"),
            "first_name": _("First Name"),
            "street": _("Street"),
            "city_zip": _("City ZIP"),
            "city_name": _("City"),
            "birth_date": _("Birth Date"),
            "gender_check": _("Gender"),
            "insurance_number": _("Insurance Number"),
            "birth_place": _("Place of Birth"),
            "disability_check": _("Disability"),
            "nationality": _("Nationality"),
            "iban": _("IBAN"),
            "bic": _("BIC"),
            "job_title": _("Job Title"),
            "emp_type_check": _("Employment Type"),
            "additional_employment_check": _("Additional Employment"),
            "minor_employment_check": _("Minor Employment"),
            "highest_edu_check": _("Highest Education"),
            "highest_training_check": _("Highest Training"),
            "weekly_hours_check": _("Weekly Working Hours"),
            "tax_id": _("Tax ID"),
            "health_insurance": _("Health Insurance"),
            "health_insurance_number": _("Health Insurance Number"),
        }

        widgets = {
            "last_name": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "first_name": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "street": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "city_zip": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "city_name": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "birth_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "insurance_number": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "birth_place": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "nationality": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "iban": forms.TextInput(attrs={"placeholder": "", "class": "form-control"}),
            "bic": forms.TextInput(attrs={"placeholder": "", "class": "form-control"}),
            "job_title": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "tax_id": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "health_insurance": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "health_insurance_number": forms.TextInput(
                attrs={"placeholder": "", "class": "form-control"}
            ),
            "gender_check": forms.RadioSelect(
                choices=PersonalInformation.GENDER_CHOICES
            ),
            "disability_check": forms.RadioSelect(
                choices=PersonalInformation.DISABILITY_CHOICES
            ),
            "emp_type_check": forms.RadioSelect(
                choices=PersonalInformation.EMPLOYMENT_TYPE_CHOICES
            ),
            "additional_employment_check": forms.RadioSelect(
                choices=PersonalInformation.ADDITIONAL_EMPLOYMENT_CHOICES
            ),
            "minor_employment_check": forms.RadioSelect(
                choices=PersonalInformation.MINOR_EMPLOYMENT_CHOICES
            ),
            "highest_edu_check": forms.RadioSelect(
                choices=PersonalInformation.HIGHEST_EDU_CHOICES
            ),
            "highest_training_check": forms.RadioSelect(
                choices=PersonalInformation.HIGHEST_TRAINING_CHOICES
            ),
            "weekly_hours_check": forms.RadioSelect(
                choices=PersonalInformation.WEEKLY_HOURS_CHOICES
            ),
        }

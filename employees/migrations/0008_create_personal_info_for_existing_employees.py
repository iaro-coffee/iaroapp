from datetime import date

from django.db import migrations


def create_personal_information_for_existing_employees(apps, schema_editor):
    EmployeeProfile = apps.get_model("employees", "EmployeeProfile")
    PersonalInformation = apps.get_model("onboarding", "PersonalInformation")

    for profile in EmployeeProfile.objects.all():
        if not profile.personal_information_form:
            familienname = profile.last_name if profile.last_name else ""
            vorname = profile.first_name if profile.first_name else ""

            personal_info = PersonalInformation.objects.create(
                familienname=familienname,
                vorname=vorname,
                strasse_hausnummer="",
                plz_ort="",
                geburtsdatum=date(2000, 1, 1),
                geschlecht="",
                versicherungsnummer="",
                geburtsort_land="",
                schwerbehindert="no",
                iban="",
                bic="",
                berufsbezeichnung="",
                ausgeubte_tatigkeit="",
                beschaftigungsart="main",
                weitere_beschaftigung="no",
                geringfugige_beschaftigung="no",
                hochster_schulabschluss="none",
                hochste_berufsausbildung="none",
                wochentliche_arbeitszeit="fulltime",
                steuer_id="",
                gesetzliche_krankenkasse="",
                unterschrift_arbeitnehmer="",
            )

            # Link the newly created form to the employee profile
            profile.personal_information_form = personal_info
            profile.onboarding_stages["personal_information"] = True
            profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0007_employeeprofile_onboarding_stages"),
        ("onboarding", "0014_alter_document_assigned_employees"),
    ]

    operations = [
        migrations.RunPython(create_personal_information_for_existing_employees),
    ]

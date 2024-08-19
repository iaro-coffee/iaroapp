from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from employees.models import EmployeeProfile


class PersonalInformation(models.Model):

    GENDER_CHOICES = [
        ("male", "Männlich"),
        ("female", "Weiblich"),
    ]

    DISABILITY_CHOICES = [
        ("yes", "Ja"),
        ("no", "Nein"),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("main", "Hauptbeschäftigung"),
        ("secondary", "Nebenbeschäftigung"),
    ]

    ADDITIONAL_EMPLOYMENT_CHOICES = [
        ("yes", "Ja"),
        ("no", "Nein"),
    ]

    MINOR_EMPLOYMENT_CHOICES = [
        ("yes", "Ja"),
        ("no", "Nein"),
    ]

    EDUCATION_CHOICES = [
        ("none", "Ohne Schulabschluss"),
        ("primary", "Haupt-/Volksschulabschluss"),
        ("secondary", "Mittlere Reife/gleichwertiger Abschluss"),
        ("higher", "Abitur/Fachabitur"),
    ]

    TRAINING_CHOICES = [
        ("none", "Ohne beruflichen Ausbildungsabschluss"),
        ("recognized", "Anerkannte Berufsausbildung"),
        ("advanced", "Meister/Techniker/gleichwertiger Fachabschluss"),
        ("bachelor", "Bachelor"),
        ("master", "Diplom/Magister/Master/Staatsexamen"),
        ("doctorate", "Promotion"),
    ]

    WORK_HOURS_CHOICES = [
        ("fulltime", "Vollzeit"),
        ("parttime", "Teilzeit"),
    ]

    # Personal info / Persönliche angaben
    familienname = models.CharField(max_length=255)
    vorname = models.CharField(max_length=255)
    strasse_hausnummer = models.CharField(max_length=255)
    plz_ort = models.CharField(max_length=100)
    geburtsdatum = models.DateField()
    geschlecht = models.CharField(max_length=10, choices=GENDER_CHOICES)
    versicherungsnummer = models.CharField(max_length=20)
    geburtsort_land = models.CharField(max_length=255)
    schwerbehindert = models.CharField(max_length=3, choices=DISABILITY_CHOICES)
    iban = models.CharField(max_length=34)
    bic = models.CharField(max_length=11)

    # Occupation details / beschaftung
    berufsbezeichnung = models.CharField(max_length=255)
    ausgeubte_tatigkeit = models.CharField(max_length=255)
    beschaftigungsart = models.CharField(max_length=10, choices=EMPLOYMENT_TYPE_CHOICES)
    weitere_beschaftigung = models.CharField(
        max_length=3, choices=ADDITIONAL_EMPLOYMENT_CHOICES
    )
    geringfugige_beschaftigung = models.CharField(
        max_length=3, choices=MINOR_EMPLOYMENT_CHOICES
    )
    hochster_schulabschluss = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    hochste_berufsausbildung = models.CharField(max_length=20, choices=TRAINING_CHOICES)
    wochentliche_arbeitszeit = models.CharField(
        max_length=10, choices=WORK_HOURS_CHOICES
    )

    # Tax and social insurance / Steuer
    steuer_id = models.CharField(max_length=11)
    gesetzliche_krankenkasse = models.CharField(max_length=255)

    # Submission
    date_submitted = models.DateField(default=timezone.now)
    unterschrift_arbeitnehmer = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.familienname}, {self.vorname} - {self.date_submitted}"


class Document(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    template_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class SignedDocument(models.Model):
    SIGNING_STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("revoked", "Revoked"),
        ("unknown", "Unknown"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    signing_url = models.URLField(max_length=1000)
    request_id = models.CharField(max_length=255, null=True, blank=True)
    action_id = models.CharField(max_length=255, null=True, blank=True)
    signing_status = models.CharField(
        max_length=20, choices=SIGNING_STATUS_CHOICES, default="not_started"
    )
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "document")

    def user_full_name(self):
        try:
            employee_profile = EmployeeProfile.objects.get(user=self.user)
            return f"{employee_profile.first_name} {employee_profile.last_name}"
        except EmployeeProfile.DoesNotExist:
            return "No Profile"

    user_full_name.short_description = "Full Name"

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from employees.models import EmployeeProfile


class PersonalInformation(models.Model):
    GENDER_CHOICES = [
        ("gender_male", _("Male")),
        ("gender_female", _("Female")),
    ]

    DISABILITY_CHOICES = [
        ("disability_yes", _("Yes")),
        ("disability_no", _("No")),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("emp_type_main", _("Main Employment")),
        ("emp_type_secondary", _("Secondary Employment")),
    ]

    ADDITIONAL_EMPLOYMENT_CHOICES = [
        ("additional_employment_yes", _("Yes")),
        ("additional_employment_no", _("No")),
    ]

    MINOR_EMPLOYMENT_CHOICES = [
        ("minor_employment_yes", _("Yes")),
        ("minor_employment_no", _("No")),
    ]

    HIGHEST_EDU_CHOICES = [
        ("highest_edu_none", _("No School Degree")),
        ("highest_edu_primary", _("Primary School")),
        ("highest_edu_secondary", _("Secondary School")),
        ("highest_edu_higher", _("High School/Abitur")),
    ]

    HIGHEST_TRAINING_CHOICES = [
        ("highest_training_none", _("No Professional Degree")),
        ("highest_training_recognized", _("Recognized Apprenticeship")),
        ("highest_training_advanced", _("Advanced Training/Technician")),
        ("highest_training_bachelor", _("Bachelor")),
        ("highest_training_master", _("Master/Diploma")),
        ("highest_training_doctorate", _("Doctorate")),
    ]

    WEEKLY_HOURS_CHOICES = [
        ("weekly_hours_fulltime", _("Full-time")),
        ("weekly_hours_halftime", _("Part-time")),
    ]

    # Personal info / Persönliche angaben
    last_name = models.CharField(max_length=255, verbose_name=_("Last Name"))
    first_name = models.CharField(max_length=255, verbose_name=_("First Name"))
    street = models.CharField(max_length=255, verbose_name=_("Street"))
    city_zip = models.CharField(max_length=10, verbose_name=_("City ZIP"))
    city_name = models.CharField(max_length=100, verbose_name=_("City"))
    birth_date = models.DateField(verbose_name=_("Birth Date"))
    gender_check = models.CharField(
        max_length=20,
        choices=[("male", _("Male")), ("female", _("Female"))],
        verbose_name=_("Gender"),
    )
    insurance_number = models.CharField(
        max_length=20, verbose_name=_("Insurance Number")
    )
    birth_place = models.CharField(max_length=255, verbose_name=_("Place of Birth"))
    disability_check = models.CharField(
        max_length=20,
        choices=[("yes", _("Yes")), ("no", _("No"))],
        verbose_name=_("Disability"),
    )
    nationality = models.CharField(max_length=100, verbose_name=_("Nationality"))
    iban = models.CharField(max_length=34, verbose_name=_("IBAN"))
    bic = models.CharField(max_length=11, verbose_name=_("BIC"))

    # Occupation details / beschaftung
    job_title = models.CharField(max_length=255, verbose_name=_("Job Title"))
    emp_type_check = models.CharField(
        max_length=20,
        choices=[
            ("main", _("Main Employment")),
            ("secondary", _("Secondary Employment")),
        ],
        verbose_name=_("Employment Type"),
    )
    additional_employment_check = models.CharField(
        max_length=30,
        choices=[("yes", _("Yes")), ("no", _("No"))],
        verbose_name=_("Additional Employment"),
    )
    minor_employment_check = models.CharField(
        max_length=30,
        choices=[("yes", _("Yes")), ("no", _("No"))],
        verbose_name=_("Minor Employment"),
    )
    highest_edu_check = models.CharField(
        max_length=30,
        choices=[
            ("none", _("No School Degree")),
            ("primary", _("Primary School")),
            ("secondary", _("Secondary School")),
            ("high", _("High School/Abitur")),
        ],
        verbose_name=_("Highest Education"),
    )
    highest_training_check = models.CharField(
        max_length=30,
        choices=[
            ("none", _("No Professional Degree")),
            ("recognized", _("Recognized Apprenticeship")),
            ("advanced", _("Advanced Training/Technician")),
            ("bachelor", _("Bachelor")),
            ("master", _("Master/Diploma")),
            ("doctorate", _("Doctorate")),
        ],
        verbose_name=_("Highest Training"),
    )
    weekly_hours_check = models.CharField(
        max_length=30,
        choices=[("full", _("Full-time")), ("part", _("Part-time"))],
        verbose_name=_("Weekly Working Hours"),
    )

    # Tax and social insurance / Steuer
    tax_id = models.CharField(max_length=11, verbose_name=_("Tax ID"))
    health_insurance = models.CharField(
        max_length=255, verbose_name=_("Health Insurance")
    )
    health_insurance_number = models.CharField(
        max_length=20, verbose_name=_("Health Insurance Number")
    )
    date_submitted = models.DateField(
        auto_now_add=True, verbose_name=_("Date Submitted")
    )

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Document(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    template_id = models.CharField(max_length=50, unique=True)
    assigned_employees = models.ManyToManyField(
        EmployeeProfile,
        blank=True,
        related_name="assigned_documents",
        help_text="Currently assigned employees",
    )
    auto_assign_new_employees = models.BooleanField(
        default=False,
        help_text="Automatically assign this document to all new employees",
    )

    def __str__(self):
        return self.name


class SignedDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    signing_url = models.URLField(max_length=1000)
    request_id = models.CharField(max_length=255, null=True, blank=True)
    action_id = models.CharField(max_length=255, null=True, blank=True)
    signing_status = models.CharField(max_length=50, default="not_started")
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


class OnboardingSlide(models.Model):
    title = models.CharField(max_length=200, verbose_name="Slide Title")
    content = CKEditor5Field(
        config_name="default", verbose_name="Slide Content", blank=True
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class OnboardingSection(models.Model):
    slide = models.ForeignKey(
        OnboardingSlide,
        related_name="sections",
        on_delete=models.CASCADE,
        verbose_name="Slide",
    )
    heading = models.CharField(max_length=200, verbose_name="Section Heading")
    details = CKEditor5Field(
        config_name="default", verbose_name="Section Details", blank=True
    )

    def __str__(self):
        return f"{self.heading} (Slide: {self.slide.title})"


class OrgChart(models.Model):
    data = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

# Generated by Django 5.0.4 on 2024-08-19 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0008_alter_signeddocument_signing_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="signeddocument",
            name="signing_status",
            field=models.CharField(
                choices=[
                    ("not_started", "Not Started"),
                    ("inprogress", "In Progress"),
                    ("success", "Completed"),
                    ("revoked", "Revoked"),
                    ("unknown", "Unknown"),
                ],
                default="not_started",
                max_length=20,
            ),
        ),
    ]

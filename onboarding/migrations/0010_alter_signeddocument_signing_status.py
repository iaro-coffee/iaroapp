# Generated by Django 5.0.4 on 2024-08-20 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0009_alter_signeddocument_signing_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="signeddocument",
            name="signing_status",
            field=models.CharField(default="not_started", max_length=50),
        ),
    ]

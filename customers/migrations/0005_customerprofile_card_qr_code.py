# Generated by Django 5.0.4 on 2024-06-17 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0004_migration_to_set_existing_emails_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerprofile",
            name="card_qr_code",
            field=models.TextField(blank=True, null=True),
        ),
    ]
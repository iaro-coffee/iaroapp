# Generated by Django 5.0.1 on 2024-01-25 18:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shifts", "0002_alter_shift_end_date_alter_shift_start_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shift",
            name="end_date",
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name="shift",
            name="start_date",
            field=models.DateTimeField(blank=True),
        ),
    ]
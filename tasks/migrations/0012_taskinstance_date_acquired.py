# Generated by Django 1.10 on 2016-09-26 08:27

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0011_auto_20160922_1029"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskinstance",
            name="date_acquired",
            field=models.DateField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]

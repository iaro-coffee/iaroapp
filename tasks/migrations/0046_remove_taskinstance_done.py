# Generated by Django 4.0.8 on 2023-08-14 23:34

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0045_alter_taskinstance_date_done"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="taskinstance",
            name="done",
        ),
    ]

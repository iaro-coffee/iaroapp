# Generated by Django 1.10 on 2016-10-11 23:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0019_taskinstance_borrower"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="taskinstance",
            options={
                "ordering": ["due_done"],
                "permissions": (("can_mark_returned", "Set task as returned"),),
            },
        ),
    ]

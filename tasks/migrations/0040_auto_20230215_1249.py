# Generated by Django 3.2.16 on 2023-02-15 12:49

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0039_alter_taskinstance_id"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="taskinstance",
            options={
                "ordering": ["date_done"],
                "permissions": (("can_mark_returned", "Set task as returned"),),
            },
        ),
        migrations.RenameField(
            model_name="taskinstance",
            old_name="due_done",
            new_name="date_done",
        ),
    ]

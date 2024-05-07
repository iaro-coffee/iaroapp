from django.db import migrations


class Migration(migrations.Migration):
    def create_types(apps, schema_editor):
        type = apps.get_model("tasks", "TaskTypes")
        type.objects.create(name="Baking")
        type.objects.create(name="Cleaning")
        type.objects.create(name="Other")

    dependencies = [
        ("tasks", "0047_tasktypes_task_type"),
    ]

    operations = [migrations.RunPython(create_types)]

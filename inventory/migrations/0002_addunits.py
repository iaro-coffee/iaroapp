from django.db import migrations


class Migration(migrations.Migration):
    def create_units(apps, schema_editor):
        unit = apps.get_model("inventory", "Units")
        unit.objects.create(name="kg")
        unit.objects.create(name="g")
        unit.objects.create(name="L")
        unit.objects.create(name="Packungen")
        unit.objects.create(name="Flaschen")

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_units)]

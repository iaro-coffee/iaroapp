from django.db import migrations


class Migration(migrations.Migration):
    def create_units(apps, schema_editor):
        unit = apps.get_model("inventory", "Units")
        unit.objects.create(name="Stück")

    dependencies = [
        ("inventory", "0006_product_modified_date"),
    ]

    operations = [migrations.RunPython(create_units)]

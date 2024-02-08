from django.db import migrations


class Migration(migrations.Migration):
    def create_types(apps, schema_editor):
        type = apps.get_model("procedures", "ProcedureCategories")
        type.objects.create(name="TestCategory1")
        type.objects.create(name="TestCategory2")

    dependencies = [
        ("procedures", "0005_procedurecategories_procedure_category"),
    ]

    operations = [migrations.RunPython(create_types)]

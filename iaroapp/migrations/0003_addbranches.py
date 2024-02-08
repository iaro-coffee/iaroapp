from django.db import migrations


class Migration(migrations.Migration):
    def create_branches(apps, schema_editor):
        branch = apps.get_model("iaroapp", "Branch")
        branch.objects.create(name="Iaro Ost")
        branch.objects.create(name="Iaro West")
        branch.objects.create(name="Iaro Space")

    dependencies = [
        ("iaroapp", "0002_alter_branch_options"),
    ]

    operations = [migrations.RunPython(create_branches)]

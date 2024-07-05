from django.db import migrations


def update_branches(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    Branch = apps.get_model("inventory", "Branch")

    branch = Branch.objects.first()

    if branch is not None:
        Profile.objects.filter(branch__isnull=True).update(branch=branch)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_profile_branch"),
    ]

    operations = [
        migrations.RunPython(update_branches),
    ]

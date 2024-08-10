from django.db import migrations


def move_profile_data(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    EmployeeProfile = apps.get_model("employees", "EmployeeProfile")

    for profile in Profile.objects.all():
        EmployeeProfile.objects.create(
            user=profile.user, avatar=profile.avatar, branch=profile.branch
        )


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(move_profile_data),
    ]

from django.db import migrations

from lib.planday import Planday


def populate_planday_id(apps, schema_editor):
    EmployeeProfile = apps.get_model("employees", "EmployeeProfile")
    planday_api = Planday()
    planday_api.authenticate()

    for profile in EmployeeProfile.objects.all():
        planday_id = planday_api.get_employee_id_by_email(profile.user.email)
        if planday_id:
            profile.planday_id = planday_id
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0003_employeeprofile_planday_id"),
    ]

    operations = [
        migrations.RunPython(populate_planday_id),
    ]

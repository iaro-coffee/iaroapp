import logging

from django.db import migrations

from lib.planday import Planday

logger = logging.getLogger(__name__)


def populate_employee_names(apps, schema_editor):
    EmployeeProfile = apps.get_model("employees", "EmployeeProfile")
    planday_instance = Planday()

    try:
        # Fetch all employees from Planday
        employees = planday_instance.get_employees()
    except Exception as e:
        logger.error(f"Failed to fetch employees from Planday: {e}")
        print(f"Failed to fetch employees from Planday: {e}")
        return

    for profile in EmployeeProfile.objects.all():
        if profile.planday_id:
            try:
                employee_details = next(
                    (
                        emp
                        for emp in employees
                        if emp.get("id") == int(profile.planday_id)
                    ),
                    None,
                )

                if employee_details:
                    profile.first_name = employee_details.get("firstName")
                    profile.last_name = employee_details.get("lastName")
                    profile.save()

                    message = (
                        f"Updated {profile.user.username} with first name "
                        f"{profile.first_name} and last name {profile.last_name}"
                    )
                    print(message)
                else:
                    warning_message = (
                        f"No matching employee found in Planday for "
                        f"{profile.user.username} with planday_id {profile.planday_id}"
                    )
                    logger.warning(warning_message)
                    print(warning_message)

            except Exception as e:
                error_message = f"Failed to update {profile.user.username}: {e}"
                logger.error(error_message)
                print(error_message)
        else:
            warning_message = (
                f"EmployeeProfile {profile.user.username} has no Planday ID"
            )
            logger.warning(warning_message)
            print(warning_message)


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0005_employeeprofile_first_name_employeeprofile_last_name"),
    ]

    operations = [
        migrations.RunPython(populate_employee_names),
    ]

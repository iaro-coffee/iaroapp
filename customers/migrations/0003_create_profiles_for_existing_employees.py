from django.db import migrations


def create_customer_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    CustomerProfile = apps.get_model("customers", "CustomerProfile")

    for user in User.objects.all():
        CustomerProfile.objects.create(user=user, is_employee=True)


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0002_alter_customerprofile_first_name_and_more"),
    ]

    operations = [
        migrations.RunPython(create_customer_profiles),
    ]

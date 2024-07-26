from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_set_default_branch_for_existing_profiles"),
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS app_users_profile;",
        ),
    ]

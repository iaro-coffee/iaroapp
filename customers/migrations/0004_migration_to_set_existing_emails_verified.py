from django.db import migrations


def create_email_records(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    EmailAddress = apps.get_model('account', 'EmailAddress')

    # remove duplicates
    for user_id in [52, 76]:
        User.objects.filter(id=user_id).update(email='{}@example.com'.format(user_id))

    for user in User.objects.exclude(email__isnull=True):
        if user.email:
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                verified=True,
                primary=True
            )


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_create_profiles_for_existing_employees'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_email_records),
    ]
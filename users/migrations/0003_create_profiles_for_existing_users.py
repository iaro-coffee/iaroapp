# Generated by Django 5.0.4 on 2024-05-16 08:14

from django.db import migrations


def create_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('users', 'Profile')
    Branch = apps.get_model('inventory', 'Branch')

    try:
        default_branch = Branch.objects.get(name='iaro West')
    except Branch.DoesNotExist:
        default_branch = None

    for user in User.objects.all():
        profile, created = Profile.objects.get_or_create(user=user)
        if not profile.branch:
            profile.branch = default_branch
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_branch'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_profiles_for_existing_users),
    ]
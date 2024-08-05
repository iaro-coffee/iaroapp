from django.db import migrations

from lib.pos_hello_tess import get_card_id_from_user


def update_customer_profiles(apps, schema_editor):
    CustomerProfile = apps.get_model("customers", "CustomerProfile")
    for profile in CustomerProfile.objects.all():
        card_id = get_card_id_from_user(profile.user)
        profile.card_qr_code = card_id
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0005_customerprofile_card_qr_code"),
    ]

    operations = [
        migrations.RunPython(update_customer_profiles),
    ]

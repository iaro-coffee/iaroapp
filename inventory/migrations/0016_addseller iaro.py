from django.db import migrations

class Migration(migrations.Migration):

    def create_seller(apps, schema_editor):
        seller = apps.get_model('inventory', 'Seller')
        seller.objects.create(name='Iaro')

    dependencies = [
        ('inventory', '0015_category_color'),
    ]

    operations = [
        migrations.RunPython(create_seller)
    ]

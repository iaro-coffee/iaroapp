from django.db import migrations

class Migration(migrations.Migration):

    def create_seller(apps, schema_editor):
        seller = apps.get_model('inventory', 'Seller')
        seller.objects.create(name='METRO')
        seller.objects.create(name='ALDI')
        seller.objects.create(name='ALNATURA')
        seller.objects.create(name='KoRo')
        seller.objects.create(name='Aryzta')
        seller.objects.create(name='Crio')
        seller.objects.create(name='Rebert')
        seller.objects.create(name='Bierhalter')
        seller.objects.create(name='Amazon')

    dependencies = [
        ('inventory', '0002_addunits'),
    ]

    operations = [
        migrations.RunPython(create_seller)
    ]

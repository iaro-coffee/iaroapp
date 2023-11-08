from django.db import migrations

class Migration(migrations.Migration):

    def create_storages(apps, schema_editor):
        unit = apps.get_model('inventory', 'Storage')
        unit.objects.create(name='Iaro Ost Bar')
        unit.objects.create(name='Iaro Ost Kühllager')
        unit.objects.create(name='Iaro Ost Tiefkühllager')
        unit.objects.create(name='Iaro Ost Trockenlager')
        unit.objects.create(name='Iaro West Bar')
        unit.objects.create(name='Iaro West Kühllaer')
        unit.objects.create(name='Iaro West Tiefkühllager')
        unit.objects.create(name='Iaro West Trockenlager')

    dependencies = [
        ('inventory', '0010_storage'),
    ]

    operations = [
        migrations.RunPython(create_storages)
    ]

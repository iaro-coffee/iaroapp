from django.db import migrations

class Migration(migrations.Migration):

    def create_types(apps, schema_editor):
        type = apps.get_model('procedures', 'ProcedureTypes')
        type.objects.create(name='Opening')
        type.objects.create(name='Closing')

    dependencies = [
        ('procedures', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_types)
    ]

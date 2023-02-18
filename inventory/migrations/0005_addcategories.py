from django.db import migrations

class Migration(migrations.Migration):

    def create_categories(apps, schema_editor):
        category = apps.get_model('inventory', 'Category')
        category.objects.create(name='Trocken')
        category.objects.create(name='Gewürze')
        category.objects.create(name='Nüsse und Trockenfrüchte')
        category.objects.create(name='Flüssig')
        category.objects.create(name='Putzmittel')
        category.objects.create(name='Tiefkühler')
        category.objects.create(name='Backzutaten')
        category.objects.create(name='Milchprodukte')
        category.objects.create(name='Obst und Gemüse')
        category.objects.create(name='Getränke')
        category.objects.create(name='Spezial')

    dependencies = [
        ('inventory', '0004_auto_20230218_1312'),
    ]

    operations = [
        migrations.RunPython(create_categories)
    ]

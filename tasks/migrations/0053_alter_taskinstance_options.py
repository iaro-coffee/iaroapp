# Generated by Django 5.0.1 on 2024-01-21 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0052_rename_weekdays_bakingplaninstance_weekday'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taskinstance',
            options={'ordering': ['date_done']},
        ),
    ]
# Generated by Django 5.0.1 on 2024-01-16 22:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0024_productstorage_main_storage'),
        ('tasks', '0050_bakingplaninstance'),
    ]

    operations = [
        migrations.AddField(
            model_name='bakingplaninstance',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.branch'),
        ),
    ]
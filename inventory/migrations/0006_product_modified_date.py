# Generated by Django 3.2.16 on 2023-02-18 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_addcategories'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='modified_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
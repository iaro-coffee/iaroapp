# Generated by Django 4.0.8 on 2023-09-20 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('procedures', '0008_alter_procedure_category'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProcedureCategories',
            new_name='ProcedureCategory',
        ),
        migrations.RenameModel(
            old_name='ProcedureTypes',
            new_name='ProcedureType',
        ),
    ]
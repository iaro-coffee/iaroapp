# Generated by Django 4.2.7 on 2023-12-03 14:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0022_alter_branch_storages"),
        ("procedures", "0009_rename_procedurecategories_procedurecategory_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedure",
            name="branch",
            field=models.ManyToManyField(
                help_text="Select seller for this product", to="inventory.branch"
            ),
        ),
    ]

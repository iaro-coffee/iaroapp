# Generated by Django 4.2.6 on 2023-11-08 12:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0012_product_storage"),
        ("iaroapp", "0004_branch_storages"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="branch",
            name="storages",
        ),
        migrations.AddField(
            model_name="branch",
            name="storages",
            field=models.ManyToManyField(default=1, to="inventory.storage"),
        ),
    ]

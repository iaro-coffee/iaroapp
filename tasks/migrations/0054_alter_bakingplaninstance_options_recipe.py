# Generated by Django 5.0.1 on 2024-01-21 18:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0024_productstorage_main_storage"),
        ("tasks", "0053_alter_taskinstance_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bakingplaninstance",
            options={
                "verbose_name": "Baking plan",
                "verbose_name_plural": "Baking plans",
            },
        ),
        migrations.CreateModel(
            name="Recipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_recipe",
                        to="inventory.product",
                    ),
                ),
            ],
        ),
    ]

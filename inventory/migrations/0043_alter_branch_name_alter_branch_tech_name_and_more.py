# Generated by Django 5.0.4 on 2024-07-11 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0042_productstorage_last_updated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="branch",
            name="name",
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="branch",
            name="tech_name",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Technical name for internal use.",
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="unit",
            field=models.ManyToManyField(
                db_index=True,
                help_text="Select unit for this product",
                to="inventory.units",
            ),
        ),
        migrations.AlterField(
            model_name="seller",
            name="name",
            field=models.CharField(
                db_index=True, help_text="Enter seller for product.", max_length=200
            ),
        ),
        migrations.AlterField(
            model_name="storage",
            name="name",
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="units",
            name="name",
            field=models.CharField(
                db_index=True, help_text="Enter unit for product.", max_length=200
            ),
        ),
    ]

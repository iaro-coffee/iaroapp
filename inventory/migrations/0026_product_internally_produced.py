# Generated by Django 5.0.1 on 2024-04-08 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0025_productstorage_threshold"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="internally_produced",
            field=models.BooleanField(default=False),
        ),
    ]

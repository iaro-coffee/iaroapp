# Generated by Django 5.0.1 on 2024-04-08 18:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0028_seller_internal"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="internally_produced",
        ),
    ]
# Generated by Django 5.0.1 on 2024-04-08 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "inventory",
            "0027_alter_product_internally_produced_alter_product_name_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="seller",
            name="internal",
            field=models.BooleanField(
                default=False,
                help_text="If this is checked the products will not show up on the shopping list but instead in production.",
            ),
        ),
    ]
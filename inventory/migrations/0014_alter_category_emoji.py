# Generated by Django 4.2.6 on 2023-11-13 12:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0013_alter_category_options_category_emoji_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="emoji",
            field=models.CharField(default="☕", max_length=10),
        ),
    ]

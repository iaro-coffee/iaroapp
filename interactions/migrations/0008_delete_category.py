# Generated by Django 5.0.4 on 2024-07-15 15:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("interactions", "0007_category_video"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Category",
        ),
    ]
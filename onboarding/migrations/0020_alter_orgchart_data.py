# Generated by Django 5.1.3 on 2024-11-27 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0019_orgchart_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orgchart',
            name='data',
            field=models.JSONField(default=list),
        ),
    ]
# Generated by Django 5.0.4 on 2024-05-31 13:34

import django.db.models.deletion
import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0032_branch_city_branch_street_address_and_more'),
        ('users', '0004_alter_profile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='branch',
            field=models.ForeignKey(blank=True, default=users.models.get_first_branch_id, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.branch'),
        ),
    ]
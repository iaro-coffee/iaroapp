# Generated by Django 5.0.1 on 2024-01-22 10:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0057_remove_recipeinstance_product_recipeinstance_recipe'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bakingplaninstance',
            name='product',
        ),
        migrations.AddField(
            model_name='bakingplaninstance',
            name='recipe',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipe_bakingplan', to='tasks.recipe'),
        ),
    ]
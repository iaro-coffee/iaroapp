# Generated by Django 5.0.4 on 2024-05-13 10:29

import django.db.models.deletion
from django.db import migrations, models, connection


def delete_invalid_task_branches(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM tasks_task_branch
            WHERE task_id NOT IN (SELECT id FROM tasks_task);
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0029_remove_product_internally_produced'),
        ('tasks', '0067_remove_task_branch_task_branch'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskinstance',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=models.CASCADE, to='inventory.Branch'),
        ),
        migrations.RunPython(delete_invalid_task_branches),
    ]
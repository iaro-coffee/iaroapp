# Generated by Django 5.0.4 on 2024-07-16 14:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0046_storage_products"),
        ("tasks", "0075_taskbranchorder"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskBranchDayOrder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="inventory.branch",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="tasks.task"
                    ),
                ),
                (
                    "weekday",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="tasks.weekdays"
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
                "unique_together": {("task", "branch", "weekday")},
            },
        ),
        migrations.DeleteModel(
            name="TaskBranchOrder",
        ),
    ]
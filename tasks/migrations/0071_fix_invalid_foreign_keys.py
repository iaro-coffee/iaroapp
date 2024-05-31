from django.db import migrations


def fix_invalid_foreign_keys(apps, schema_editor):
    TaskBranchThrough = apps.get_model("tasks", "Task_branch")
    Task = apps.get_model("tasks", "Task")

    valid_task_ids = Task.objects.values_list('id', flat=True)
    print(' VALID ENTRIES:', valid_task_ids)
    invalid_entries = TaskBranchThrough.objects.exclude(task_id__in=valid_task_ids)
    print(' INVALID ENTRIES:', list(invalid_entries))
    invalid_entries.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0070_remove_taskinstance_description_alter_task_branch_and_more'),
        ('inventory', '0029_remove_product_internally_produced'),
    ]

    operations = [
        migrations.RunPython(fix_invalid_foreign_keys),
    ]

# Generated by Django 5.0.4 on 2024-05-13 15:24

import ckeditor.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('inventory', '0029_remove_product_internally_produced'),
        ('tasks', '0069_fill_branch_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskinstance',
            name='description',
        ),
        migrations.AlterField(
            model_name='task',
            name='branch',
            field=models.ManyToManyField(blank=True, help_text='Select which branches should be assigned for the task. <br>', related_name='tasks', to='inventory.branch'),
        ),
        migrations.AlterField(
            model_name='task',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='Select which groups should be assigned for the task. <br>', to='auth.group'),
        ),
        migrations.AlterField(
            model_name='task',
            name='summary',
            field=ckeditor.fields.RichTextField(blank=True, help_text='Enter a brief description of the task. <br>', max_length=1000),
        ),
        migrations.AlterField(
            model_name='task',
            name='types',
            field=models.ManyToManyField(help_text='Select a type for this task. <br>', to='tasks.tasktypes'),
        ),
        migrations.AlterField(
            model_name='task',
            name='users',
            field=models.ManyToManyField(blank=True, help_text='Select which users should be assigned for the task. <br>', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='weekdays',
            field=models.ManyToManyField(blank=True, help_text='Select weekdays for this task. <br>', to='tasks.weekdays'),
        ),
    ]
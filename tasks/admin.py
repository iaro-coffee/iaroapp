from django.contrib import admin

# Register your models here.

from .models import Author, Category, Task, TaskInstance

"""Minimal registration of Models.
admin.site.register(Task)
admin.site.register(Author)
admin.site.register(TaskInstance)
admin.site.register(Category)
"""

admin.site.register(Category)

class TasksInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Task


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration object for Author models.
    Defines:
     - fields to be displayed in list view (list_display)
     - orders fields in detail view (fields),
       grouping the date fields horizontally
     - adds inline addition of tasks in author view (inlines)
    """
    list_display = ('last_name',
                    'first_name', 'date_of_joined', 'date_of_quited')
    fields = ['first_name', 'last_name', ('date_of_joined', 'date_of_quited')]
    inlines = [TasksInline]


class TasksInstanceInline(admin.TabularInline):
    """Defines format of inline task instance insertion (used in TaskAdmin)"""
    model = TaskInstance


class TaskAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('title', 'author', 'display_category')
    inlines = [TasksInstanceInline]


admin.site.register(Task, TaskAdmin)


@admin.register(TaskInstance)
class TaskInstanceAdmin(admin.ModelAdmin):
    """Administration object for TaskInstance models.
    Defines:
     - fields to be displayed in list view (list_display)
     - filters that will be displayed in sidebar (list_filter)
     - grouping of fields into sections (fieldsets)
    """
    list_display = ('task', 'status', 'borrower', 'due_done', 'id')
    list_filter = ('status', 'due_done')

    fieldsets = (
        (None, {
            'fields': ('task', 'description', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_done', 'borrower')
        }),
    )

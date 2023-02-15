from django.contrib import admin
from .models import User, Weekdays, Task, TaskInstance

class TasksInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""
    model = Task

class TasksInstanceInline(admin.TabularInline):
    """Defines format of inline task instance insertion (used in TaskAdmin)"""
    model = TaskInstance

class TaskAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """
    list_display = ('title', 'display_users', 'display_groups', 'display_weekdays')
    inlines = [TasksInstanceInline]


admin.site.register(Task, TaskAdmin)

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



# Custom admin view added to display groups in user table
# and hide mail address

from django.utils.safestring import mark_safe
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib import admin

def roles(self):
    #short_name = unicode # function to get group name
    short_name = lambda x:str(x).upper() # first letter of a group
    p = sorted([u"<a title='%s'>%s</a>" % (x, short_name(x)) for x in self.groups.all()])
    if self.user_permissions.count(): p += ['+']
    value = ', '.join(p)
    return mark_safe("<nobr>%s</nobr>" % value)
roles.allow_tags = True
roles.short_description = u'Groups'

def last(self):
    fmt = "%b %d, %H:%M"
    #fmt = "%Y %b %d, %H:%M:%S"
    if self.last_login:
        value = self.last_login.strftime(fmt)
    else:
        value = "Never"
    return mark_safe("<nobr>%s</nobr>" % value)
last.allow_tags = True
last.admin_order_field = 'last_login'

def adm(self):
    return self.is_superuser
adm.boolean = True
adm.admin_order_field = 'is_superuser'

from django.urls import reverse

def persons(self):
    return ', '.join(['%s' % (x.username) for x in self.user_set.all().order_by('username')])
persons.allow_tags = True

class UserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', roles, last]
    list_filter = ['groups', 'is_superuser', 'is_active']

class GroupAdmin(GroupAdmin):
    list_display = ['name', persons]
    list_display_links = ['name']

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)

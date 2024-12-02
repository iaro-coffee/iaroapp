from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.utils.safestring import mark_safe

from .forms import RecipeForm
from .models import BakingPlanInstance, Recipe, RecipeInstance, Task, TaskInstance


class TasksInline(admin.TabularInline):
    """Defines format of inline task insertion (used in AuthorAdmin)"""

    model = Task
    extra = 0


class TasksInstanceInline(admin.TabularInline):
    """Defines format of inline task instance insertion (used in TaskAdmin)"""

    model = TaskInstance


@admin.action(description="Duplicate selected tasks")
def duplicate_tasks(modeladmin, request, queryset):
    for task in queryset:
        task.pk = None
        task.save()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Administration object for Task models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of task instances in task view (inlines)
    """

    list_display = ("title", "display_users", "display_groups", "display_weekdays")
    list_filter = (
        "weekdays",
        "groups",
        "branch",
    )
    search_fields = ["title"]
    # inlines = [TasksInstanceInline] # if we need this - need to add pagination and fix error of toomanyfields on edit
    actions = [duplicate_tasks]


class TaskInstanceAdmin(admin.ModelAdmin):
    """Administration object for TaskInstance models.
    Defines:
     - fields to be displayed in list view (list_display)
     - filters that will be displayed in sidebar (list_filter)
     - grouping of fields into sections (fieldsets)
    """

    list_display = ("task", "user", "done", "date_done", "id")
    list_filter = ("done", "date_done")

    fieldsets = (
        (None, {"fields": ("task", "description", "id")}),
        ("Availability", {"fields": ("done", "date_done", "user")}),
    )


# Custom admin view added to display groups in user table
# and hide mail address


@admin.display(description="Groups")
def roles(self):
    # short_name = unicode # function to get group name
    def short_name(x):
        return str(x).upper()  # first letter of a group

    p = sorted(
        ["<a title='{}'>{}</a>".format(x, short_name(x)) for x in self.groups.all()]
    )
    if self.user_permissions.count():
        p += ["+"]
    value = ", ".join(p)
    return mark_safe("<nobr>%s</nobr>" % value)  # nosec


@admin.display(ordering="last_login")
def last(self):
    fmt = "%b %d, %H:%M"
    # fmt = "%Y %b %d, %H:%M:%S"
    if self.last_login:
        value = self.last_login.strftime(fmt)
    else:
        value = "Never"
    return mark_safe("<nobr>%s</nobr>" % value)  # nosec


@admin.display(
    boolean=True,
    ordering="is_superuser",
)
def adm(self):
    return self.is_superuser


def persons(self):
    return ", ".join(
        ["%s" % (x.username) for x in self.user_set.all().order_by("username")]
    )


class UserAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", roles, last]
    list_filter = ["groups", "is_superuser", "is_active"]


class GroupAdmin(GroupAdmin):
    list_display = ["name", persons]
    list_display_links = ["name"]


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)


@admin.register(BakingPlanInstance)
class BakingPlanInstanceAdmin(admin.ModelAdmin):
    list_display = ["recipe", "value", "display_weekdays", "branch"]

    @admin.display(description="Weekday")
    def display_weekdays(self, obj):
        return ", ".join([weekday.name for weekday in obj.weekday.all()])


class RecipeInstanceInline(admin.TabularInline):
    """Defines format of inline recipe instance insertion (used in RecipeAdmin)"""

    model = RecipeInstance
    list_display = (
        "incredient",
        "quantity",
        "product_unit",
        "preparation",
    )
    readonly_fields = ("product_unit",)

    @admin.display(description="Unit")
    def product_unit(self, obj):
        return obj.product_unit


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeForm
    list_display = ["name", "product"]
    inlines = [RecipeInstanceInline]

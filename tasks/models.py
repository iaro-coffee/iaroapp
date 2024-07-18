from datetime import date

from django.contrib.auth.models import User  # Required to assign User as a user
from django.contrib.auth.models import Group
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from iaroapp.base_model import BaseModel
from inventory.models import Branch, Product
from tasks.task_types import TaskTypes


class Weekdays(BaseModel):
    name = models.CharField(max_length=200, help_text="Enter task weekdays.")

    def __str__(self):
        return self.name


class Task(BaseModel):
    """Model representing a task (but not a specific copy of a task)."""

    title = models.CharField(max_length=200)
    users = models.ManyToManyField(
        User,
        help_text="Select which users should be assigned for the task. <br>",
        blank=True,
    )
    groups = models.ManyToManyField(
        Group,
        help_text="Select which groups should be assigned for the task. <br>",
        blank=True,
    )
    weekdays = models.ManyToManyField(
        Weekdays, help_text="Select weekdays for this task. <br>", blank=True
    )
    types = models.ManyToManyField(
        TaskTypes, help_text="Select a type for this task. <br>"
    )
    summary = CKEditor5Field(
        max_length=1000,
        help_text="Enter a brief description of the task. <br>",
        null=True,
        blank=True,
        config_name="default",
    )
    branch = models.ManyToManyField(
        "inventory.Branch",
        related_name="tasks",
        help_text="Select which branches should be assigned for the task. <br>",
        blank=True,
    )
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subtasks",
    )

    def is_done(self, branch):
        if self.subtasks.all():
            return all(subtask.is_done(branch) for subtask in self.subtasks.all())
        else:
            today = timezone.now().date()
            return self.taskinstance_set.filter(
                date_done__date=today, branch=branch
            ).exists()

    @property
    def get_types(self):
        return self.types.all()

    @property
    def assignees(self):
        return ", ".join(
            [groups.name for groups in self.groups.all()]
            + [users.get_username() for users in self.users.all()]
        )

    def display_users(self):
        return ", ".join([users.get_username() for users in self.users.all()[:3]])

    display_users.short_description = "Users"

    def display_groups(self):
        return ", ".join([groups.name for groups in self.groups.all()[:3]])

    display_groups.short_description = "Groups"

    def display_weekdays(self):
        return ", ".join([weekdays.name for weekdays in self.weekdays.all()[:3]])

    display_weekdays.short_description = "Weekdays"

    def get_absolute_url(self):
        """Returns the url to access a particular task instance."""
        return reverse("task-detail", args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title


class TaskInstance(BaseModel):
    """Model representing a specific copy of a task (i.e. that can be borrowed from the library)."""

    task = models.ForeignKey("Task", on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_done = models.DateTimeField(null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)

    @property
    def is_overdue(self):
        """Determines if the task is overdue based on due date and current date."""
        return bool(self.date_done and date.today() > self.date_done)

    class Meta:
        ordering = ["date_done"]

    def __str__(self):
        """String for representing the Model object."""
        return "{} ({})".format(self.id, self.task.title)


class TaskBranchDayOrder(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    weekday = models.ForeignKey(Weekdays, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("task", "branch", "weekday")
        ordering = ["order"]

    def __str__(self):
        return f"{self.task.title} ({self.branch.name} - {self.weekday.name})"


class Recipe(BaseModel):
    name = models.CharField(max_length=200, blank=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_recipe"
    )

    def __str__(self):
        return self.name


class RecipeInstance(BaseModel):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_instances", null=True
    )
    incredient = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    quantity = models.FloatField()
    preparation = models.BooleanField(default=False)

    @property
    def product_unit(self):
        return (
            self.incredient.unit.first().name if self.incredient.unit.exists() else None
        )


class BakingPlanInstance(BaseModel):
    """Model representing the relationship between a product and a storage."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_bakingplan", null=True
    )
    value = models.FloatField()
    weekday = models.ManyToManyField(
        Weekdays, help_text="Select weekdays for this task"
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Baking plan"
        verbose_name_plural = "Baking plans"


# Create baking plan tasks


def create_or_update_baking_plan(preparation, weekday, items):
    kitchen_group, _ = Group.objects.get_or_create(name="Kitchen")
    baking_type, _ = TaskTypes.objects.get_or_create(name="Baking")

    if preparation:
        title = "Vorbereitungsplan Backen"
    else:
        title = "Backplan"

    weekday_names = [day.name for day in weekday]
    existing_task = Task.objects.filter(
        title=title, weekdays__name__in=weekday_names
    ).distinct()

    summary = (
        """
        <h1>"""
        + title
        + """</h1>
        <table border="1" cellpadding="1" cellspacing="1" style="width:300px">
            <thead>
                <tr>
                    <td><strong>Ost</strong></td>
                    <td><strong>West</strong></td>
                    <td><strong>Vorbereitung</strong></td>
                </tr>
            </thead>
            <tbody>"""
    )
    for item in items:
        summary += (
            "<tr><td>"
            + str(item["value_ost"])
            + "</td><td>"
            + str(item["value_west"])
            + "</td><td>"
            + str(item["name"])
            + "</td></tr>"
        )
    summary += """
            </tbody>
        </table>
    """

    if existing_task.exists():
        task = existing_task.first()
        task.summary = summary
        task.save()
    else:
        task = Task.objects.create(title=title, summary=summary)
        task.save()
        task.groups.add(kitchen_group)
        task.weekdays.set(weekday)
        task.types.add(baking_type)


def merge_list(items):
    merged_items = {}

    for item in items:
        name = item["name"]
        value_ost = item["value_ost"]
        value_west = item["value_west"]

        if name in merged_items:
            # If the name is already in merged_items, add the values
            merged_item = merged_items[name]
            merged_item["value_ost"] = (merged_item["value_ost"] or 0) + (
                value_ost or 0
            )
            merged_item["value_west"] = (merged_item["value_west"] or 0) + (
                value_west or 0
            )
        else:
            # If the name is not in merged_items, add the new item
            merged_items[name] = {
                "value_ost": value_ost or 0,
                "value_west": value_west or 0,
                "name": name,
            }

    # Convert the merged_items back to a list of dictionaries
    return list(merged_items.values())


@receiver(post_save, sender=BakingPlanInstance)
def baking_plan_instance_post_save(sender, instance, created, **kwargs):
    def on_commit():
        if not created:
            items = []
            items_preparation = []
            weekday = instance.weekday.all()
            baking_plan_instances = BakingPlanInstance.objects.filter(
                weekday__in=weekday
            )
            for baking_plan_instance in baking_plan_instances:
                multiplier = baking_plan_instance.value
                branch = str(baking_plan_instance.branch)
                recipe = baking_plan_instance.recipe
                recipe_instances = recipe.recipe_instances.all()
                for recipe_instance in recipe_instances:
                    name = recipe_instance.incredient
                    preparation = recipe_instance.preparation
                    if not preparation:
                        multiplier = 1
                    if branch == "Iaro Ost":
                        value_ost = int(multiplier * recipe_instance.quantity)
                        value_west = None
                    else:
                        value_west = int(multiplier * recipe_instance.quantity)
                        value_ost = None
                    if preparation:
                        items_preparation.append(
                            {
                                "value_ost": value_ost,
                                "value_west": value_west,
                                "name": name,
                            }
                        )
                    else:
                        items.append(
                            {
                                "value_ost": value_ost,
                                "value_west": value_west,
                                "name": name,
                            }
                        )
                    items_preparation = merge_list(items_preparation)
                    items = merge_list(items)

            weekday_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            current_weekday_name = weekday.first().name
            current_weekday_index = weekday_names.index(current_weekday_name)
            previous_weekday_index = (current_weekday_index - 1) % 7
            previous_weekday_name = weekday_names[previous_weekday_index]
            previous_weekday = Weekdays.objects.filter(name=previous_weekday_name)

            create_or_update_baking_plan(True, previous_weekday, items_preparation)
            create_or_update_baking_plan(False, weekday, items)

    transaction.on_commit(on_commit)


post_save.connect(baking_plan_instance_post_save, sender=BakingPlanInstance)

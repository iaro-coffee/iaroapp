from django.db import models
from django.urls import reverse

class Weekdays(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Enter task weekdays."
        )

    def __str__(self):
        return self.name

from django.contrib.auth.models import User, Group
from ckeditor.fields import RichTextField

class Task(models.Model):
    """Model representing a task (but not a specific copy of a task)."""
    title = models.CharField(max_length=200)
    users = models.ManyToManyField(User, help_text="Select which users should be assigned for the task", blank=True)
    groups = models.ManyToManyField(Group, help_text="Select which groups should be assigned for the task", blank=True)
    weekdays = models.ManyToManyField(Weekdays, help_text="Select weekdays for this task")
    summary = RichTextField(max_length=1000, help_text="Enter a brief description of the task", blank=True)

    def display_users(self):
        return ', '.join([users.get_username() for users in self.users.all()[:3]])
    display_users.short_description = 'Users'

    def display_groups(self):
        return ', '.join([groups.name for groups in self.groups.all()[:3]])
    display_groups.short_description = 'Groups'

    def display_weekdays(self):
        return ', '.join([weekdays.name for weekdays in self.weekdays.all()[:3]])
    display_weekdays.short_description = 'Weekdays'

    def get_absolute_url(self):
        """Returns the url to access a particular task instance."""
        return reverse('task-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title


from datetime import date
from django.contrib.auth.models import User  # Required to assign User as a user

class TaskInstance(models.Model):
    """Model representing a specific copy of a task (i.e. that can be borrowed from the library)."""
    task = models.ForeignKey('Task', on_delete=models.RESTRICT, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=200, blank=True)
    date_done = models.DateField(null=True, blank=True)

    @property
    def is_overdue(self):
        """Determines if the task is overdue based on due date and current date."""
        return bool(self.date_done and date.today() > self.date_done)

    done = models.BooleanField()

    class Meta:
        ordering = ['date_done']
        permissions = (("can_mark_returned", "Set task as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return '{0} ({1})'.format(self.id, self.task.title)
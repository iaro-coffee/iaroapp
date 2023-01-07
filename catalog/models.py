from django.db import models

# Create your models here.

from django.urls import reverse  # To generate URLS by reversing URL patterns


class Category(models.Model):
    """Model representing a task category (e.g. Science Fiction, Non Fiction)."""
    name = models.CharField(
        max_length=200,
        help_text="Enter a task category (e.g. Science Fiction, French Poetry etc.)"
        )

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Task(models.Model):
    """Model representing a task (but not a specific copy of a task)."""
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    # Foreign Key used because task can only have one author, but authors can have multiple tasks
    # Author as a string rather than object because it hasn't been declared yet in file.
    summary = models.TextField(max_length=1000, help_text="Enter a brief description of the task")
    category = models.ManyToManyField(Category, help_text="Select a category for this task")
    # ManyToManyField used because a category can contain many tasks and a Task can cover many categorys.
    # Category class has already been defined so we can specify the object above.
    
    class Meta:
        ordering = ['title', 'author']

    def display_category(self):
        """Creates a string for the Category. This is required to display category in Admin."""
        return ', '.join([category.name for category in self.category.all()[:3]])

    display_category.short_description = 'Category'

    def get_absolute_url(self):
        """Returns the url to access a particular task instance."""
        return reverse('task-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title


import uuid  # Required for unique task instances
from datetime import date

from django.contrib.auth.models import User  # Required to assign User as a borrower


class TaskInstance(models.Model):
    """Model representing a specific copy of a task (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text="Unique ID for this particular task across whole library")
    task = models.ForeignKey('Task', on_delete=models.RESTRICT, null=True)
    description = models.CharField(max_length=200)
    due_done = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        """Determines if the task is overdue based on due date and current date."""
        return bool(self.due_done and date.today() > self.due_done)

    LOAN_STATUS = (
        ('d', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='d',
        help_text='Task availability')

    class Meta:
        ordering = ['due_done']
        permissions = (("can_mark_returned", "Set task as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return '{0} ({1})'.format(self.id, self.task.title)


class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_joined = models.DateField(null=True, blank=True)
    date_of_quited = models.DateField('quited', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return '{0}, {1}'.format(self.last_name, self.first_name)

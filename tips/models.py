from django.db import models
from django.urls import reverse

class Tips(models.Model):
    """Model representing a task (but not a specific copy of a task)."""
    title = models.CharField(max_length=200)
    
    def get_absolute_url(self):
        """Returns the url to access a particular task instance."""
        return reverse('task-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title

import uuid

# class TipsInstance(models.Model):
#     """Model representing a specific copy of a task (i.e. that can be borrowed from the library)."""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4,
#                           help_text="Unique ID for this particular task across whole library")
#     task = models.ForeignKey('Task', on_delete=models.RESTRICT, null=True)
#     description = models.CharField(max_length=200)
#     due_done = models.DateField(null=True, blank=True)

#     @property
#     def is_overdue(self):
#         """Determines if the task is overdue based on due date and current date."""
#         return bool(self.due_done and date.today() > self.due_done)

#     LOAN_STATUS = (
#         ('d', 'Maintenance'),
#         ('o', 'On loan'),
#         ('a', 'Available'),
#         ('r', 'Reserved'),
#     )

#     status = models.CharField(
#         max_length=1,
#         choices=LOAN_STATUS,
#         blank=True,
#         default='d',
#         help_text='Task availability')

#     class Meta:
#         ordering = ['due_done']
#         permissions = (("can_mark_returned", "Set task as returned"),)

#     def __str__(self):
#         """String for representing the Model object."""
#         return '{0} ({1})'.format(self.id, self.task.title)
from ckeditor.fields import RichTextField
from django.db import models
from procedures.procedure_type import ProcedureType
from procedures.procedure_category import ProcedureCategory
from django.contrib.auth.models import Group

class Procedure(models.Model):
    """Model representing a task (but not a specific copy of a procedure)."""
    title = models.CharField(max_length=200)
    type = models.ManyToManyField(ProcedureType, help_text="Select a type for this procedure")
    summary = RichTextField(max_length=1000, help_text="Enter a brief description of the task", blank=True)
    groups = models.ManyToManyField(Group, help_text="Select which groups should be assigned for the task", blank=True)
    category = models.ForeignKey(ProcedureCategory, on_delete=models.PROTECT, help_text="Select which category should be assigned for the task", blank=True, null=True)
    date_done = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return self.title
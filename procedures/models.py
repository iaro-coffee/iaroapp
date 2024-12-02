from django.contrib.auth.models import Group
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from iaroapp.base_model import BaseModel
from inventory.models import Branch
from procedures.procedure_category import ProcedureCategory
from procedures.procedure_type import ProcedureType


class Procedure(BaseModel):
    """Model representing a task (but not a specific copy of a procedure)."""

    title = models.CharField(max_length=200)
    type = models.ManyToManyField(
        ProcedureType, help_text="Select a type for this procedure"
    )
    summary = CKEditor5Field(
        "Summary",
        config_name="extends",
        help_text="Enter a brief description of the task",
        blank=True,
    )
    groups = models.ManyToManyField(
        Group,
        help_text="Select which groups should be assigned for the task",
        blank=True,
    )
    category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        help_text="Select which category should be assigned for the task",
        blank=True,
        null=True,
    )
    branch = models.ManyToManyField(Branch, help_text="Select seller for this product")
    date_done = models.DateTimeField(null=True, blank=True)

    def display_branch(self):
        return ", ".join([branch.name for branch in self.branch.all()])

    display_branch.short_description = "Branches"

    def __str__(self):
        """String for representing the Model object."""
        return self.title

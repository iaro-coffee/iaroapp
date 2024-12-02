from django.contrib.auth.models import User
from django.db import models

from iaroapp.base_model import BaseModel
from ratings.models import EmployeeRating


class Shift(BaseModel):
    """Model representing a shift (but not a specific copy of a tip)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    rating = models.ForeignKey(
        EmployeeRating, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        """String for representing the Model object."""
        return "shift"

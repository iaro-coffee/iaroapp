from django.contrib.auth.models import User
from django.db import models

from iaroapp.base_model import BaseModel


class EmployeeRating(BaseModel):
    """Model representing a tip (but not a specific copy of a tip)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    rating = models.FloatField()

    def __str__(self):
        """String for representing the Model object."""
        return "rating"

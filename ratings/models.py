from django.contrib.auth.models import User
from django.db import models

from iaroapp.base_model import BaseModel


class EmployeeRating(BaseModel):
    """Model representing an employee's shift rating."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    rating = models.FloatField()
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Rating: {self.rating} for {self.user.username} on {self.date}"

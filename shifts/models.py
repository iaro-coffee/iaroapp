from django.contrib.auth.models import User
from django.db import models

from iaroapp.base_model import BaseModel
from ratings.models import EmployeeRating


class Shift(BaseModel):
    """Model representing a shift."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    planday_shift_id = models.IntegerField(null=True, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    rating = models.ForeignKey(
        EmployeeRating, on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        return (
            f"Shift for {self.user.username} from {self.start_date} to {self.end_date}"
        )

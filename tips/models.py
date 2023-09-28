from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class AssignedTip(models.Model):
    """Model representing a tip (but not a specific copy of a tip)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    note = models.CharField(max_length=50, default="Tip")
    amount = models.FloatField()

    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse('tip-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.note

class Tip(models.Model):
    """Model representing a tip (but not a specific copy of a tip)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    note = models.CharField(max_length=50, default="Tip")
    amount = models.FloatField()
    
    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse('tip-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.note
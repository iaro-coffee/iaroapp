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
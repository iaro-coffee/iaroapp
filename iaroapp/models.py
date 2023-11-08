from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

from inventory.models import Storage

class Branch(models.Model):
    """Model representing a storage location."""
    name = models.CharField(max_length=500)
    storages = models.ManyToManyField(Storage, default=1)

    class Meta:
         verbose_name_plural = 'Branches'

    def display_storages(self):
        return ", ".join([storage.name for storage in self.storages.all()])
    display_storages.short_description = 'Storages'

    def __str__(self):
        """String for representing the Model object."""
        return self.name
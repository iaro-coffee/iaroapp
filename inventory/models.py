from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Units(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Enter unit for product."
        )

    def __str__(self):
        return self.name

class Seller(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Enter seller for product."
        )

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Enter seller for product."
        )

    def __str__(self):
        return self.name

class Product(models.Model):
    """Model representing a tip (but not a specific copy of a tip)."""
    name = models.CharField(max_length=500)
    unit = models.ManyToManyField(Units, help_text="Select unit for this product")
    value = models.FloatField()
    value_intended = models.FloatField()
    threshold = models.FloatField(default=0)
    category = models.ManyToManyField(Category, help_text="Select category for this product")
    seller = models.ManyToManyField(Seller, help_text="Select seller for this product")
    modified_date = models.DateTimeField(auto_now=True)

    @property
    def value_tobuy(self):
        return abs(float(self.value-self.value_intended))

    def display_category(self):
        return ', '.join([category.name for category in self.category.all()[:3]])
    display_category.short_description = 'Categories'

    def display_unit(self):
        return ', '.join([unit.name for unit in self.unit.all()[:3]])
    display_unit.short_description = 'Unit'

    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse('product-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.name
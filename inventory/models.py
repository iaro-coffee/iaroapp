from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import re

def sanitize_string(string):
  string = re.sub(r"[äöüß]", lambda x: x.group(0).encode("utf-8").hex(), string)
  string = re.sub(r"[^a-zA-Z0-9_]", "_", string)
  return string

class Storage(models.Model):
    """Model representing a storage location."""
    name = models.CharField(max_length=500)

    def __str__(self):
        """String for representing the Model object."""
        return self.name

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
        help_text="Enter category for product."
    )
    emoji = models.CharField(
        max_length=10,
        default="☕")

    class Meta:
         verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    # Add a calculated field called name_encoded
    @property
    def name_encoded(self):
        # Use the sanitize function to encode the name
        return sanitize_string(self.name)

class Product(models.Model):
    """Model representing a product."""
    name = models.CharField(max_length=500)
    unit = models.ManyToManyField(Units, help_text="Select unit for this product")
    value = models.FloatField()
    value_intended = models.FloatField()
    category = models.ManyToManyField(Category, help_text="Select category for this product")
    seller = models.ManyToManyField(Seller, help_text="Select seller for this product")
    modified_date = models.DateTimeField(auto_now=True)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, default=1)

    @property
    def tobuy(self):
        return (((100/self.value_intended)*self.value) < 30)

    @property
    def value_tobuy(self):
        return abs(float(self.value-self.value_intended))
    
    def display_seller(self):
        return self.seller.all()[0].name
    display_seller.short_description = 'Seller'

    def display_category(self):
        return ', '.join([category.name for category in self.category.all()[:3]])
    display_category.short_description = 'Categories'

    def display_unit(self):
        return ', '.join([unit.name for unit in self.unit.all()[:3]])
    display_unit.short_description = 'Unit'

    def display_storage(self):
        return self.storage.name
    display_storage.short_description = 'Storage'

    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse('product-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.name
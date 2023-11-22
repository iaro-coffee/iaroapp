from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from colorful.fields import RGBColorField
from django.utils.html import format_html
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
    color = RGBColorField(default='')

    class Meta:
         verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    # Add a calculated field called name_encoded
    @property
    def name_encoded(self):
        # Use the sanitize function to encode the name
        return sanitize_string(self.name)

    def display_color(self):
        return format_html('<span style="width:15px;height:15px;display:block;background-color:{}"></span>', self.color)
    display_color.short_description = 'Color'

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

    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse('product-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.name

# Generated ToDos from inventory updates
from django.db.models.signals import post_save
from django.dispatch import receiver
from tasks.models import Task, User, Group, Weekdays, TaskTypes

@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    if instance.seller.filter(name='Iaro Kitchen').exists():
        product_name = instance.name
        product_storage = instance.storage
        if float(instance.value) < float(instance.value_intended):
            order_text = "%s for %s" % (instance.name, instance.storage)
            task = Task(title=order_text)
            task.save()
            group = Group.objects.get(name='Kitchen')
            tasktype = TaskTypes.objects.get(name='Baking')
            task.groups.add(group)
            task.type.add(tasktype)

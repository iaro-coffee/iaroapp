from colorful.fields import RGBColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import SET_NULL, Sum
from django.template import Library
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify

from iaroapp.base_model import BaseModel


class Storage(BaseModel):
    """Model representing a storage location."""

    name = models.CharField(max_length=500)
    color = RGBColorField(default="")

    def display_color(self):
        return format_html(
            '<span style="width:15px;height:15px;display:block;background-color:{}"></span>',
            self.color,
        )

    display_color.short_description = "Color"

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Branch(BaseModel):
    """Model representing iaro department and storages location associated with it"""

    name = models.CharField(max_length=500)
    tech_name = models.CharField(
        max_length=500, blank=True, help_text="Technical name for internal use."
    )
    storages = models.ManyToManyField(
        Storage,
        related_name="branches",
        help_text="Storages associated with this branch.",
    )
    departmentId = models.CharField(
        max_length=500,
        default="",
        help_text="Department ID associated with the branch.",
    )
    street_address = models.CharField(
        max_length=500,
        default="Sophienstraße 108",
        help_text="Street address of the branch.",
    )
    city = models.CharField(
        max_length=500,
        default="Karlsruhe",
        help_text="City where the branch is located.",
    )

    class Meta:
        verbose_name_plural = "Branches"

    @property
    def get_storages(self):
        """Returns all storages associated with this branch."""
        return self.storages.all()

    def display_storages(self):
        """Displays a comma-separated list of storage names for admin interface."""
        return ", ".join([storage.name for storage in self.storages.all()])

    display_storages.short_description = "Storages"

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def save(self, *args, **kwargs):
        """Override the save method to set the technical name if not provided."""
        if not self.tech_name:
            self.tech_name = slugify(self.name)
        super().save(*args, **kwargs)


class Units(BaseModel):
    name = models.CharField(max_length=200, help_text="Enter unit for product.")

    def __str__(self):
        return self.name


class Seller(BaseModel):
    class VisibilityChoices(models.TextChoices):
        SHOPPING_LIST = "shopping_list", "Shopping List"
        PRODUCTION = "production", "Production"
        NOWHERE = "nowhere", "Nowhere"

    class WeekdayChoices(models.TextChoices):
        MONDAY = "monday", "Monday"
        TUESDAY = "tuesday", "Tuesday"
        WEDNESDAY = "wednesday", "Wednesday"
        THURSDAY = "thursday", "Thursday"
        FRIDAY = "friday", "Friday"
        SATURDAY = "saturday", "Saturday"
        SUNDAY = "sunday", "Sunday"

    name = models.CharField(max_length=200, help_text="Enter seller for product.")
    visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.NOWHERE,
        help_text="Controls where products from this seller appear.",
    )
    is_weekly = models.BooleanField(
        default=False,
        help_text="Check if the products of this seller are ordered weekly",
    )
    order_weekday = models.CharField(
        max_length=20,
        choices=WeekdayChoices.choices,
        default=WeekdayChoices.MONDAY,
        help_text="If you checked previous option, specify the day on which you order at this seller",
    )

    class Meta:
        verbose_name_plural = "Sellers"

    def __str__(self):
        return self.name


register = Library()


class Product(BaseModel):
    """Model representing a product."""

    name = models.CharField(max_length=500, unique=True)
    unit = models.ManyToManyField(Units, help_text="Select unit for this product")
    seller = models.ForeignKey(
        Seller,
        help_text="Select seller for this product",
        on_delete=SET_NULL,
        null=True,
    )
    modified_date = models.DateTimeField(auto_now=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="Select the branch to define on which shopping list this product should appear",
    )
    hint = models.TextField(
        null=True,
        blank=True,
        help_text="Enter hint for doing inventory. (e.g. Only count 6 packs)",
    )

    @property
    def has_main_storage(self):
        for product_storage in self.product_storages.all():
            if product_storage.main_storage:
                return True
        return False

    def get_main_storage(self):
        for product_storage in self.product_storages.all():
            if product_storage.main_storage:
                return product_storage.storage
        return False

    def needs_packaging(self):
        if self.has_main_storage and self.has_shortage:
            for product_storage in self.product_storages.all():
                if not product_storage.main_storage and product_storage.has_shortage:
                    return True
        return False

    @property
    def has_shortage(self):
        for product_storage in self.product_storages.all():
            if product_storage.has_shortage:
                return True
        return False

    @property
    def value_to_buy(self):
        total_value = self.product_storages.aggregate(total_value=Sum("value"))[
            "total_value"
        ]
        total_value_intended = self.product_storages.aggregate(
            total_value_intended=Sum("value_intended")
        )["total_value_intended"]
        if total_value is None or total_value_intended is None:
            return 0

        if self.seller.is_weekly:
            return total_value_intended
        else:
            return float(total_value_intended - total_value)

    def get_oos_value_shipping(self):
        product_storage_dict = {}
        for branch in self.get_storage_branches:
            value_needed = 0
            for product_storage in self.product_storages.all():
                if not product_storage.main_storage and product_storage.has_shortage:
                    if branch == product_storage.branch:
                        value_needed = value_needed + product_storage.value_needed
            product_storage_dict[branch] = {
                "value_needed": value_needed,
            }
        return product_storage_dict

    @property
    def storages(self):
        return [
            product_storage.storage for product_storage in self.product_storages.all()
        ]

    @property
    def get_storage_branches(self):
        return [
            product_storage.branch for product_storage in self.product_storages.all()
        ]

    def display_seller(self):
        return (
            {"name": self.seller.name, "order_weekday": self.seller.order_weekday}
            if self.seller
            else None
        )

    display_seller.short_description = "Seller"

    def display_unit(self):
        return ", ".join([unit.name for unit in self.unit.all()[:3]])

    display_unit.short_description = "Unit"

    def display_availability(self):
        total_value = self.product_storages.aggregate(total_value=Sum("value"))[
            "total_value"
        ]
        total_value_intended = self.product_storages.aggregate(
            total_value_intended=Sum("value_intended")
        )["total_value_intended"]
        if total_value is None or total_value_intended is None:
            return ""
        if self.has_shortage:
            color = "red"
        else:
            color = ""
        return format_html(
            '<span style="color:{}">{}/{}</span>',
            *(color, round(total_value), round(total_value_intended))
        )

    display_availability.short_description = "Availability"

    def get_absolute_url(self):
        """Returns the url to access a particular tip instance."""
        return reverse("product-detail", args=[str(self.id)])

    def get_product_storage(self):
        product_storage_dict = {}
        for storage in self.product_storages.all():
            if storage.value_intended and storage.value:
                product_storage_dict[storage.storage] = {
                    "value": storage.value,
                    "value_intended": storage.value_intended,
                    "has_shortage": (
                        ((100 / storage.value_intended) * storage.value)
                        < storage.threshold
                    ),
                }
            else:
                product_storage_dict[storage.storage] = {
                    "value": storage.value,
                    "value_intended": storage.value_intended,
                    "has_shortage": True,
                }
        return product_storage_dict

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class ProductStorage(BaseModel):
    """Model representing the relationship between a product and a storage."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_storages"
    )
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE)
    value = models.FloatField()
    value_intended = models.FloatField()
    threshold = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(0.0)],
        help_text="Enter the amount of the item, when it needs to get bought.",
    )
    main_storage = models.BooleanField(default=False)

    @property
    def value_needed(self):
        return self.value_intended - self.value

    @property
    def has_shortage(self):
        if self.value and self.value_intended:
            return self.value < self.threshold
        return True

    @property
    def branch(self):
        branches = Branch.objects.all()
        for branch in branches:
            if self.storage in branch.storages.all():
                return branch
        return None

    # Update the product item to refresh the modified_date attribute
    def save(self, *args, **kwargs):
        self.product.save()
        super().save(*args, **kwargs)


# Generated ToDos from inventory updates


# @receiver(post_save, sender=Product)
# def product_post_save(sender, instance, created, **kwargs):
#     if instance.seller.filter(name='Iaro Kitchen').exists():
#         product_name = instance.name
#         product_storages = instance.storages
#         if float(instance.value) < float(instance.value_intended):
#             order_text = "%s for %s" % (instance.name, instance.storages)
#             task = Task(title=order_text)
#             task.save()
#             group = Group.objects.get(name='Kitchen')
#             tasktype = TaskTypes.objects.get(name='Baking')
#             task.groups.add(group)
#             task.type.add(tasktype)

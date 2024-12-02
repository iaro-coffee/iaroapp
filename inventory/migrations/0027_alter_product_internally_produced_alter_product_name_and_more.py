import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0026_product_internally_produced"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="internally_produced",
            field=models.BooleanField(
                default=False,
                help_text="If this is checked the product will not show up on the shopping list.",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=500, unique=True),
        ),
        migrations.AlterField(
            model_name="productstorage",
            name="threshold",
            field=models.IntegerField(
                default=30,
                help_text="Enter the amount of the item, when it needs to get bought.",
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]

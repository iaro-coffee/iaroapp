# Generated by Django 5.0.4 on 2024-07-26 11:23

import django.db.models.deletion
import django_ckeditor_5.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("interactions", "0008_delete_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearningCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name="video",
            name="description",
            field=django_ckeditor_5.fields.CKEditor5Field(
                blank=True, null=True, verbose_name="Description"
            ),
        ),
        migrations.CreateModel(
            name="PDFUpload",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="pdfs/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="interactions.learningcategory",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PDFImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", models.ImageField(upload_to="pdf_images/")),
                ("page_number", models.IntegerField()),
                (
                    "pdf",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="interactions.pdfupload",
                    ),
                ),
            ],
        ),
    ]
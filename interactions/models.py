from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from embed_video.fields import EmbedVideoField

from inventory.models import Branch


class Note(models.Model):
    sender = models.ForeignKey(
        User, related_name="sent_notes", on_delete=models.CASCADE
    )
    receivers = models.ManyToManyField(User, related_name="received_notes")
    branches = models.ManyToManyField(Branch, related_name="branch_notes", blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"Note from {self.sender.username} at {self.timestamp}"


class NoteReadStatus(models.Model):
    note = models.ForeignKey(
        Note, related_name="read_statuses", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="note_read_statuses", on_delete=models.CASCADE
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ("note", "user")
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["note", "user"]),
        ]


class Video(models.Model):
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = CKEditor5Field(
        "Description", blank=True, null=True, config_name="default"
    )
    video_file = models.FileField(upload_to="videos/", blank=True, null=True)
    video_url = EmbedVideoField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        if not self.video_file and not self.video_url:
            raise ValidationError("You must provide a video file or a video URL.")

        if self.video_file and self.video_url:
            raise ValidationError(
                "You cannot provide both a video file and a video URL."
            )

    class Meta:
        ordering = ["-added_at"]


class LearningCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Learning Category"
        verbose_name_plural = "Learning Categories"


class PDFUpload(models.Model):
    file = models.FileField(upload_to="pdfs/")
    name = models.CharField(max_length=255)
    description = CKEditor5Field(config_name="default", blank=True, null=True)
    category = models.ForeignKey(
        LearningCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    branches = models.ManyToManyField(Branch, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        pdf_images = PDFImage.objects.filter(pdf=self)
        for pdf_image in pdf_images:
            pdf_image.image.delete()
            pdf_image.delete()

        self.file.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "PDF Upload"
        verbose_name_plural = "PDF Uploads"


class PDFImage(models.Model):
    pdf = models.ForeignKey(PDFUpload, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="pdf_images/")
    page_number = models.IntegerField()

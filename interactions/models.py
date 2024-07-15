from django.contrib.auth.models import User
from django.db import models

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
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to="videos/")

    def __str__(self):
        return self.title

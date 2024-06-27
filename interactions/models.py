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
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"Note from {self.sender.username} at {self.timestamp}"

from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    sender = models.ForeignKey(
        User, related_name="sent_notes", on_delete=models.CASCADE
    )
    receivers = models.ManyToManyField(User, related_name="received_notes")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note from {self.sender.username} to {self.receivers.count()} receivers at {self.timestamp}"

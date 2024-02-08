from django.db import models


class TaskTypes(models.Model):
    name = models.CharField(max_length=200, help_text="Enter task type.")

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

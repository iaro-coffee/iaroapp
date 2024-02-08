from django.db import models

from iaroapp.base_model import BaseModel


class ProcedureType(BaseModel):
    name = models.CharField(max_length=200, help_text="Enter procedure type.")

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

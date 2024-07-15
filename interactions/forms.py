from django import forms
from django.contrib.auth.models import User

from inventory.models import Branch

from .models import Note, Video


class NoteForm(forms.ModelForm):
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(), required=False, label="Send to Branches"
    )
    receivers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(), required=False, label="Send to Users"
    )

    class Meta:
        model = Note
        fields = ["content", "receivers", "branches"]

    def clean(self):
        cleaned_data = super().clean()
        receivers = cleaned_data.get("receivers")
        branches = cleaned_data.get("branches")

        if not receivers and not branches:
            raise forms.ValidationError(
                "Please select at least one receiver or one branch."
            )

        return cleaned_data

    def save(self, commit=True, sender=None):
        note = super().save(commit=False)
        if sender:
            note.sender = sender

        note.save()  # Ensure the note instance is saved to the database and has an ID

        branches = self.cleaned_data.get("branches")
        if branches:
            users_in_branches = User.objects.filter(
                profile__branch__in=branches
            ).distinct()
            note.receivers.add(*users_in_branches)

        if commit:
            self.save_m2m()

        return note


class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["category", "title", "description", "video_file"]

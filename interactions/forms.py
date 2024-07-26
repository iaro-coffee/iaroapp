from django import forms
from django.contrib.auth.models import User

from inventory.models import Branch

from .models import LearningCategory, Note, PDFUpload, Video


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


class PDFUploadForm(forms.ModelForm):
    new_category = forms.CharField(
        max_length=255,
        required=False,
        help_text="Enter a new category name if you want to create one.",
    )

    class Meta:
        model = PDFUpload
        fields = ["file", "name", "description", "category"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = LearningCategory.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        new_category_name = cleaned_data.get("new_category")
        category = cleaned_data.get("category")

        if not category and not new_category_name:
            raise forms.ValidationError(
                "You must select a category or enter a new category name."
            )

        if new_category_name:
            category, created = LearningCategory.objects.get_or_create(
                name=new_category_name
            )
            cleaned_data["category"] = category
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_category_name = self.cleaned_data.get("new_category")
        if new_category_name:
            category, created = LearningCategory.objects.get_or_create(
                name=new_category_name
            )
            instance.category = category
        if commit:
            instance.save()
        return instance

from urllib.parse import parse_qs, urlparse

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
        fields = ["category", "title", "description", "video_file", "video_url"]

    def clean_video_url(self):
        video_url = self.cleaned_data.get("video_url")
        if video_url:
            if "youtube.com" in video_url or "youtu.be" in video_url:
                parsed_url = urlparse(video_url)
                if parsed_url.netloc == "youtu.be":
                    video_id = parsed_url.path[1:]
                    return f"https://www.youtube.com/embed/{video_id}"
                elif (
                    parsed_url.netloc == "www.youtube.com"
                    and parsed_url.path == "/watch"
                ):
                    video_id = parse_qs(parsed_url.query).get("v")
                    if video_id:
                        return f"https://www.youtube.com/embed/{video_id[0]}"
        return video_url

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get("video_file")
        video_url = cleaned_data.get("video_url")

        if not video_file and not video_url:
            raise forms.ValidationError("You must provide a video file or a video URL.")

        if video_file and video_url:
            raise forms.ValidationError(
                "You cannot provide both a video file and a video URL."
            )

        cleaned_data["video_url"] = self.clean_video_url()

        return cleaned_data


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

from django import forms
from django.contrib.auth.models import User

from inventory.models import Branch

from .models import Note


class NoteForm(forms.ModelForm):
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(), required=False, label="Send to Branches"
    )

    class Meta:
        model = Note
        fields = ["content", "receivers", "branches"]
        widgets = {
            "receivers": forms.CheckboxSelectMultiple(),
            "branches": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        receivers = cleaned_data.get("receivers")
        branches = cleaned_data.get("branches")

        if not receivers and not branches:
            raise forms.ValidationError(
                "Please select at least one receiver or one branch."
            )

        return cleaned_data

    def save(self, commit=True):
        note = super().save(commit=False)
        branches = self.cleaned_data.get("branches")

        if commit:
            note.save()

        if branches:
            users_in_branches = User.objects.filter(
                profile__branch__in=branches
            ).distinct()
            note.receivers.add(*users_in_branches)

        if commit:
            note.save()
            self.save_m2m()

        return note

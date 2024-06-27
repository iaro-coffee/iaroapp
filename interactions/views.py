from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from .forms import NoteForm
from .models import Note, NoteReadStatus


class NoteView(LoginRequiredMixin, TemplateView):
    template_name = "view_notes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = NoteForm()

        user = self.request.user
        user_branch = user.profile.branch

        # Fetch received notes (combine by user and by user's branch) - init load, first 5
        received_notes = (
            Note.objects.filter(Q(receivers=user) | Q(branches=user_branch))
            .distinct()
            .order_by("-timestamp")[:10]
        )

        # Mark notes as read for the current user
        for note in received_notes:
            read_status, created = NoteReadStatus.objects.get_or_create(
                note=note, user=user
            )
            if not read_status.is_read:
                read_status.is_read = True
                read_status.save()

        # Fetch sent notes
        sent_notes = self.request.user.sent_notes.all().order_by("-timestamp")[:10]

        context["received_notes"] = received_notes
        context["sent_notes"] = sent_notes
        context["pageTitle"] = "Notes"
        return context

    def post(self, request, *args, **kwargs):
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False, sender=request.user)
            note.save()
            form.save_m2m()

            # Create NoteReadStatus entries for each recipient
            receivers = form.cleaned_data["receivers"]
            branches = form.cleaned_data["branches"]
            all_recipients = set(receivers)

            # Add all users in the specified branches
            for branch in branches:
                all_recipients.update(User.objects.filter(profile__branch=branch))

            for recipient in all_recipients:
                NoteReadStatus.objects.create(note=note, user=recipient, is_read=False)

            return redirect("view_notes")
        else:
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)


class LoadMoreNotesView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        offset = int(request.GET.get("offset", 0))
        limit = 5
        user = request.user
        user_branch = user.profile.branch

        received_notes = list(
            Note.objects.filter(Q(receivers=user) | Q(branches=user_branch))
            .distinct()
            .order_by("-timestamp")[offset : offset + limit]
        )

        sent_notes = list(
            user.sent_notes.all().order_by("-timestamp")[offset : offset + limit]
        )

        data = {
            "received_notes": [
                self.note_to_dict(note, user_branch) for note in received_notes
            ],
            "sent_notes": [self.note_to_dict(note, user_branch) for note in sent_notes],
        }

        return JsonResponse(data)

    def note_to_dict(self, note, user_branch):
        return {
            "sender_username": note.sender.username if note.sender else None,
            "sender_avatar": (
                note.sender.profile.avatar.url
                if note.sender and note.sender.profile.avatar
                else ""
            ),
            "content": note.content,
            "timestamp_date": note.timestamp.strftime("%B %d"),
            "timestamp_time": note.timestamp.strftime("%H:%M"),
            "branches": (
                [{"name": branch.name} for branch in note.branches.all()]
                if note.branches.exists()
                else None
            ),
        }


class UnreadCountView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        user_branch = user.profile.branch

        unread_count = NoteReadStatus.objects.filter(
            Q(user=user)
            & Q(is_read=False)
            & (Q(note__receivers=user) | Q(note__branches=user_branch))
        ).count()

        return JsonResponse({"unread_count": unread_count})

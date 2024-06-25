from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .forms import NoteForm
from .models import Note


class NoteView(LoginRequiredMixin, TemplateView):
    template_name = "view_notes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = NoteForm()

        # Fetch received notes
        received_notes = Note.objects.filter(receivers=self.request.user)

        # Fetch the branch of the current user
        user_branch = self.request.user.profile.branch
        if user_branch:
            branch_notes = Note.objects.filter(branches=user_branch)
        else:
            branch_notes = Note.objects.none()

        combined_notes = list(set(received_notes) | set(branch_notes))

        context["received_notes"] = combined_notes
        context["sent_notes"] = self.request.user.sent_notes.all()
        return context

    def post(self, request, *args, **kwargs):
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False, sender=request.user)
            note.save()
            form.save_m2m()
            return redirect("view_notes")
        else:
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)

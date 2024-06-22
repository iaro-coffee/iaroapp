from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import NoteForm


@login_required
def send_note_view(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.sender = request.user
            note.save()
            form.save_m2m()
            return redirect("view_notes")
    else:
        form = NoteForm()
    return render(request, "send_note.html", {"form": form})


@login_required
def view_notes_view(request):
    received_notes = request.user.received_notes.all()
    sent_notes = request.user.sent_notes.all()
    return render(
        request,
        "view_notes.html",
        {"received_notes": received_notes, "sent_notes": sent_notes},
    )

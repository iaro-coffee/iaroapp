from django.urls import path

from .views import LoadMoreNotesView, NoteView

urlpatterns = [
    path("", NoteView.as_view(), name="view_notes"),
    path("load-more-notes/", LoadMoreNotesView.as_view(), name="load_more_notes"),
]

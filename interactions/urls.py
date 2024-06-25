from django.urls import path

from .views import NoteView

urlpatterns = [
    path("", NoteView.as_view(), name="view_notes"),
]

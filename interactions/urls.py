from django.urls import path

from . import views

urlpatterns = [
    path("send/", views.send_note_view, name="send_note"),
    path("view/", views.view_notes_view, name="view_notes"),
]

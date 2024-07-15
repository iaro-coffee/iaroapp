from django.urls import path

from .views import (
    LoadMoreNotesView,
    NoteView,
    UnreadCountView,
    VideoListView,
    VideoUploadView,
)

urlpatterns = [
    path("", NoteView.as_view(), name="view_notes"),
    path("load-more-notes/", LoadMoreNotesView.as_view(), name="load_more_notes"),
    path("get-unread-count/", UnreadCountView.as_view(), name="get_unread_count"),
    path("upload-video/", VideoUploadView.as_view(), name="upload_video"),
    path("videos/", VideoListView.as_view(), name="view_videos"),
]

from django.urls import path

from .views import (
    LoadMoreNotesView,
    NoteView,
    UnreadCountView,
    VideoListView,
    VideoUploadView,
    get_conversion_details,
    get_conversion_status,
    upload_pdf,
    view_slides,
    view_slides_list,
)

urlpatterns = [
    path("", NoteView.as_view(), name="view_notes"),
    path("load-more-notes/", LoadMoreNotesView.as_view(), name="load_more_notes"),
    path("get-unread-count/", UnreadCountView.as_view(), name="get_unread_count"),
    path("upload-video/", VideoUploadView.as_view(), name="upload_video"),
    path("videos/", VideoListView.as_view(), name="view_videos"),
    path("upload-pdf/", upload_pdf, name="upload_pdf"),
    path("learning/", view_slides_list, name="view_slides_list"),
    path("learning/<int:pdf_id>/", view_slides, name="view_slides"),
    path("conversion_details/", get_conversion_details, name="conversion_details"),
    path("conversion_status/", get_conversion_status, name="conversion_status"),
]

from django.urls import path

from .views import DocumentSignView, DocumentsListView, PersonalInformationView

urlpatterns = [
    path(
        "personal-information/",
        PersonalInformationView.as_view(),
        name="personal_information",
    ),
    path("documents/", DocumentsListView.as_view(), name="documents_list"),
    path(
        "document-sign/<int:document_id>/",
        DocumentSignView.as_view(),
        name="document_sign",
    ),
]

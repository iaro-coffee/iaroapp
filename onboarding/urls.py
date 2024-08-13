from django.urls import path

from . import views
from .views import PersonalInformationView

urlpatterns = [
    path(
        "personal-information/",
        PersonalInformationView.as_view(),
        name="personal_information",
    ),
    path("sign-documents/", views.sign_document, name="sign_documents"),
]

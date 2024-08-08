from django.urls import path

from .views import PersonalInformationView

urlpatterns = [
    path(
        "personal-information/",
        PersonalInformationView.as_view(),
        name="personal_information",
    ),
]

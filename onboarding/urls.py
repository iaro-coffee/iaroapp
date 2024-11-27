from django.urls import path

from .views import (
    DocumentSignView,
    DocumentsListView,
    InitialInformationView,
    OrgChartView,
    PersonalInformationView,
)

app_name = "onboarding"

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
    path('api/org-chart/', OrgChartView.as_view(), name='org_chart_api'),
    path("onboarding/", InitialInformationView.as_view(), name="onboarding"),
]

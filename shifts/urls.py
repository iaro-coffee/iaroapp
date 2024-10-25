from django.urls import path

from .views import ShiftManagementView

urlpatterns = [
    path("manage/", ShiftManagementView.as_view(), name="shift-management"),
]

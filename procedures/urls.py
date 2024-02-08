from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="procedures"),
    path("opening", views.opening, name="opening"),
    path("closing", views.closing, name="closing"),
]

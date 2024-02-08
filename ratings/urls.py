from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="ratings"),
    path("evaluation", views.ratings_evaluation, name="ratings_evaluation"),
    path(
        "evaluation/<int:id>/",
        views.user_ratings_evaluation,
        name="user_ratings_evaluation",
    ),
]

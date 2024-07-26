from django.urls import path

from . import views
from .views import TasksEvaluationView, TasksView

urlpatterns = [
    path("", TasksView.as_view(), name="tasks"),
    path("evaluation", TasksEvaluationView.as_view(), name="tasks_evaluation"),
    path("baking", views.tasks_baking, name="tasks_baking"),
    path("add", views.tasks_add, name="tasks_add"),
    path("<int:taskId>", views.task_single, name="task_single"),
]

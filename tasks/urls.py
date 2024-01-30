from django.urls import path
from . import views

urlpatterns = [
    path('', views.tasks, name='tasks'),
    path('evaluation', views.tasks_evaluation, name='tasks_evaluation'),
    path('baking', views.tasks_baking, name='tasks_baking'),
    path('add', views.tasks_add, name='tasks_add'),
]
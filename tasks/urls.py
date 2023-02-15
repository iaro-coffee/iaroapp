from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('overview', views.tasks, name='tasks')
]
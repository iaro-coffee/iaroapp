from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Task, User, TaskInstance, Weekdays

def index(request):
    return render(
        request,
        'index.html'
    )

from django.views import generic

class TaskListView(generic.ListView):
    model = Task
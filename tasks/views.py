from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Task, User, TaskInstance, Weekdays
from django.forms.models import model_to_dict
import datetime

def index(request):
    return render(
        request,
        'index.html'
    )

def tasks(request):

    weekdayToday = datetime.datetime.today().strftime('%A')
    tasks = Task.objects.all()
    myTasks = []
    for task in tasks:
        task = model_to_dict(task)
        for weekday in task['weekdays']:
            if weekdayToday == str(weekday):
                for group in request.user.groups.all():
                    if request.user in task['users'] or group in task['groups']:
                        myTasks.append(task)

    return render(
        request,
        'tasks.html',
        context={
            'task_list': myTasks,
        },
    )
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Task, User, TaskInstance, Weekdays
from django.forms.models import model_to_dict
import datetime
from django.http import HttpResponse
import json

def index(request):

    if request.method == 'POST':

        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        taskids_completed = list(form_data.keys())
        date = datetime.datetime.now()
        today_date = datetime.datetime.today().strftime('%Y-%m-%d')

        for task_id in taskids_completed:
            task = Task.objects.get(id=task_id)
            TaskInstance.objects.create(user=user, date_done=date, task=task, done=True)
    
        return HttpResponse(200)

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
        task['assignees'] = task['users'] + task['groups']
        for weekday in task['weekdays']:
            if weekdayToday == str(weekday):
                if request.user in task['users']:
                    task['done'] = False
                    myTasks.append(task)
                else:
                    for group in request.user.groups.all():
                        if group in task['groups']:
                            task['done'] = False
                            myTasks.append(task)
                            break

    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:

        for task in myTasks:
            if task['id'] == task_instance.task.id:
                if [task_instance.date_done.strftime('%A') == weekday for weekday in task['weekdays']]:
                    today = datetime.datetime.now().date()
                    task_day = task_instance.date_done
                    if ((today-task_day).days < 7):
                        task['done'] = True


    return render(
        request,
        'tasks.html',
        context={
            'task_list': myTasks,
        },
    )

from django.contrib.auth.decorators import user_passes_test

def check_admin(user):
   return user.is_superuser

@user_passes_test(check_admin)
def tasks_evaluation(request):

    tasks = Task.objects.all()
    tasks_evaluation = {}
    weekdays = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]
    weekdayToday = datetime.datetime.today().strftime('%A')

    for weekday in weekdays:
        tasks_evaluation[weekday] = []
        for task in tasks:
            task = model_to_dict(task)
            task['assignees'] = task['users'] + task['groups']
            for task_weekday in task['weekdays']:
                if weekday == str(task_weekday):
                    tasks_evaluation[weekday].append(task)

    beginning_of_week = datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday() % 7)
    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:

        for weekday in weekdays:
            for task in tasks_evaluation[weekday]:
                if task['id'] == task_instance.task.id:
                    if beginning_of_week.date() < task_instance.date_done:
                        task['done'] = "True"
                    else:
                        task['done'] = "False"

    return render(
        request,
        'tasks_evaluation.html',
        context={
            'tasks': tasks_evaluation,
            'weekdays': weekdays,
            'today': weekdayToday
        },
    )
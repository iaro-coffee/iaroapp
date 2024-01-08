from django.shortcuts import render
from .models import Task, TaskInstance
from django.forms.models import model_to_dict
from datetime import datetime, timedelta, time
from operator import itemgetter
from inventory.models import Product
from django.contrib.auth import get_user_model
import json
from django.http import HttpResponse

def getMyTasks(request):
    weekdayToday = datetime.today().strftime('%A')
    tasks = Task.objects.all()
    myTasks = []
    for task in tasks:
        task = model_to_dict(task)
        task['assignees'] = task['users'] + task['groups']
        userMatch = request.user in task['users']
        groupMatch = any(group in request.user.groups.all() for group in task['groups'])
        weekdayMatch = weekdayToday in [str(weekday) for weekday in task['weekdays']]
        if (userMatch or groupMatch) and (weekdayMatch or not task['weekdays']):
            task['done'] = False
            myTasks.append(task)

    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:
        for task in myTasks:
            if task['id'] == task_instance.task.id:
                if task_instance.date_done != None:
                    if [task_instance.date_done.strftime('%A') == weekday for weekday in task['weekdays']]:
                        task['date_done'] = task_instance.date_done

    return sorted(myTasks, key=itemgetter('type'))

def tasks(request):

    User = get_user_model()

    if request.method == 'POST':

        print("were into post")
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        taskids_completed = list(form_data.keys())
        date = datetime.now()

        for task_id in taskids_completed:
            task = Task.objects.get(id=task_id)
            TaskInstance.objects.create(user=user, date_done=date, task=task)

        return HttpResponse(200)

    return render(
        request,
        'tasks.html',
        context={
            'task_list': getMyTasks(request),
            'today': datetime.today().date()
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
    weekdayToday = datetime.today().strftime('%A')

    for weekday in weekdays:
        tasks_evaluation[weekday] = []
        for task in tasks:
            task = model_to_dict(task)
            task['assignees'] = task['users'] + task['groups']
            for task_weekday in task['weekdays']:
                if weekday == str(task_weekday):
                    tasks_evaluation[weekday].append(task)

    beginning_of_week = datetime.combine(datetime.today() - timedelta(days=datetime.today().weekday() % 7), time())
    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:
        for weekday in weekdays:
            for task in tasks_evaluation[weekday]:
                if 'done' not in task:
                    task['done'] = {}
                if task['id'] == task_instance.task.id:
                    if task_instance.date_done != None:
                        if beginning_of_week.astimezone() < task_instance.date_done:
                            done = {}
                            done['done_weekday'] = weekdays[task_instance.date_done.weekday()]
                            done['done_datetime'] = task_instance.date_done.strftime("%d.%m, %H:%M")
                            done['done_persons'] = task_instance.user
                            task['done'][weekdays[task_instance.date_done.weekday()]] = done

    return render(
        request,
        'tasks_list_evaluation.html',
        context={
            'tasks': tasks_evaluation,
            'weekdays': weekdays,
            'today': weekdayToday
        },
    )

@user_passes_test(check_admin)
def tasks_baking(request):

    products = Product.objects.filter(seller__name='Iaro Kitchen')

    return render(
        request,
        'tasks_baking.html',
        context={
            'products': products,
        },
    )
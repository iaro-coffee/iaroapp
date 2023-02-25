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
        task_id = list(form_data.keys())[0]
        user = User.objects.get(id=user_id)
        date = datetime.datetime.now()
        task = Task.objects.get(id=task_id)
        today_date = datetime.datetime.today().strftime('%Y-%m-%d')

        is_action_add_task = bool(form_data[next(iter(form_data))])

        if is_action_add_task:
            TaskInstance.objects.create(user=user, date_done=date, task=task, done=True)
        else:
            for task_instance in TaskInstance.objects.all():
                task_date = task_instance.date_done.strftime('%Y-%m-%d')
                if task_date == today_date:
                    if int(task_instance.task.id) == int(task_id):
                        TaskInstance.objects.filter(id=task_instance.id).delete()
    
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
                    task['done'] = True

    return render(
        request,
        'tasks.html',
        context={
            'task_list': myTasks,
        },
    )
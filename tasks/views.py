from django.shortcuts import render

from iaroapp.cron import assignTips
from .models import Task, TaskInstance
from django.forms.models import model_to_dict
from datetime import datetime, timedelta, time
from django.http import HttpResponse
import json
from django.contrib.auth import get_user_model
from tips.models import AssignedTip
from lib import planday
from operator import itemgetter

planday = planday.Planday()
run_once_day = {}
nextShifts = []
nextShiftsUser = {}
showOpening = False
showClosing = False

def shiftsWereCheckedToday(userId):
    if userId not in run_once_day or run_once_day[userId] != datetime.today().date():
        return False
    return True

def getShowOpening(request):
    if not shiftsWereCheckedToday(request.user.id):
        getNextShiftsByUser(request)
    return showOpening

def getShowClosing(request):
    if not shiftsWereCheckedToday(request.user.id):
        getNextShiftsByUser(request)
    return showClosing

def getNextShiftsByUser(request):
    global nextShifts
    global nextShiftsUser
    global showOpening
    global showClosing
    today = datetime.today().date()
    if not shiftsWereCheckedToday(request.user.id):
        planday.authenticate()
        nextShifts = planday.get_upcoming_shifts(None, None)
        run_once_day[request.user.id] = today
        userShifts = []
        for shift in nextShifts:
            if request.user.email == shift['employee']:
                start = datetime.fromisoformat(shift["start"]).strftime('%H.%M')
                end = datetime.fromisoformat(shift["end"]).strftime('%H.%M')
                day = datetime.fromisoformat(shift["end"]).strftime('%d')
                weekday = datetime.fromisoformat(shift["end"]).strftime('%a')
                userShifts.append({"day": day, "start": start, "end": end, "weekday": weekday})
                shiftdayString = datetime.fromisoformat(shift["start"]).strftime('%Y-%m-%d')
                if shiftdayString == str(today) and start == '07.30':
                    showOpening = True
                if shiftdayString == str(today) and end == '18.30':
                    showClosing = True
        nextShiftsUser[request.user.id] = userShifts
    return nextShiftsUser[request.user.id]


def index(request):
    User = get_user_model()

    if request.method == 'POST':
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

    allTips = AssignedTip.objects.filter(user=request.user, date__month__gte=datetime.now().strftime("%m"))
    tips = []

    for tip in allTips:
        tips.append(model_to_dict(tip))

    tipsSum = 0
    for tip in tips:
        tipsSum += tip['amount']

    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)

    myTasks = getMyTasks(request)
    return render(
        request,
        'index.html',
        context={
            'tipsSum': tipsSum,
            'tips': tips,
            'nextShifts': userShifts,
            'task_list': myTasks[0:len(myTasks) if len(myTasks) <= 3 else 3],
            'today': today,
        }
    )

def getMyTasks(request):
    weekdayToday = datetime.today().strftime('%A')
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
                if task_instance.date_done != None:
                    if [task_instance.date_done.strftime('%A') == weekday for weekday in task['weekdays']]:
                        task['date_done'] = task_instance.date_done

    return sorted(myTasks, key=itemgetter('type'))

def tasks(request):
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
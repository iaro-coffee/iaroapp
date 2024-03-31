from datetime import datetime, timedelta

from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from lib import planday
from shifts.models import Shift
from tasks.models import TaskInstance
from tasks.views import getMyTasks

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
    if not request.user.is_authenticated:
        return {}
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
            if request.user.email == shift["employee"]:
                if "departmentId" not in request.session:
                    request.session["departmentId"] = shift["departmentId"]
                start = datetime.fromisoformat(shift["start"]).strftime("%H.%M")
                end = datetime.fromisoformat(shift["end"]).strftime("%H.%M")
                day = datetime.fromisoformat(shift["end"]).strftime("%d")
                weekday = datetime.fromisoformat(shift["end"]).strftime("%a")
                userShifts.append(
                    {"day": day, "start": start, "end": end, "weekday": weekday}
                )
                shiftdayString = datetime.fromisoformat(shift["start"]).strftime(
                    "%Y-%m-%d"
                )
                if shiftdayString == str(today) and start == "07.30":
                    showOpening = True
                if shiftdayString == str(today) and end == "18.30":
                    showClosing = True
        nextShiftsUser[request.user.id] = userShifts
    return nextShiftsUser[request.user.id]


def hasOngoingShift(request):
    if not request.user.is_authenticated:
        return False
    try:
        return (
            True,
            Shift.objects.filter(user=request.user, end_date=None)
            .first()
            .start_date.timestamp(),
        )
    except:
        return False, None


def getTasksDoneLastMonth(request):
    return TaskInstance.objects.filter(
        user=request.user,
        date_done__lte=datetime.today(),
        date_done__gt=datetime.today() - timedelta(days=30),
    ).count()


def index(request):
    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)
    myTasks = getMyTasks(request)
    ongoingShift = hasOngoingShift(request)
    tasksDoneLastMonth = getTasksDoneLastMonth(request)
    print(ongoingShift)
    return render(
        request,
        "index.html",
        context={
            "pageTitle": "Dashboard",
            "nextShifts": userShifts,
            "task_list": myTasks[0 : len(myTasks) if len(myTasks) <= 3 else 3],
            "tasks_done_last_month": tasksDoneLastMonth,
            "today": today,
            "ongoingShift": ongoingShift[0],
            "shiftStart": ongoingShift[1],
        },
    )


def login(request, *args, **kwargs):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    else:
        return auth_views.LoginView.as_view()(request, *args, **kwargs)

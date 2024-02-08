from django.shortcuts import render

from tasks.models import Task, TaskInstance
from django.forms.models import model_to_dict
from datetime import datetime, timedelta, time
from lib import planday
from operator import itemgetter
from inventory.models import Product

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
                if not "departmentId" in request.session:
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


from tasks.views import getMyTasks


def index(request):
    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)
    myTasks = getMyTasks(request)

    return render(
        request,
        "index.html",
        context={
            "nextShifts": userShifts,
            "task_list": myTasks[0 : len(myTasks) if len(myTasks) <= 3 else 3],
            "today": today,
        },
    )


from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import views as auth_views


def login(request, *args, **kwargs):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    else:
        return auth_views.LoginView.as_view()(request, *args, **kwargs)

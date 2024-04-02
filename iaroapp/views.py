import json
from datetime import datetime, timedelta

from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from lib import planday
from ratings.views import EmployeeRating
from shifts.models import Shift
from tasks.models import TaskInstance
from tasks.views import getMyTasks

planday = planday.Planday()
run_once_day = {}
run_once_day_punch_clock = {}
nextShifts = []
nextShiftsUser = {}
showOpening = False
showClosing = False
punchClockRecordsUser = {}


def shiftsWereCheckedToday(userId):
    if userId not in run_once_day or run_once_day[userId] != datetime.today().date():
        return False
    return True


def punchClockRecordsWereCheckedToday(userId):
    if (
        userId not in run_once_day_punch_clock
        or run_once_day_punch_clock[userId] != datetime.today().date()
    ):
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
    now = timezone.now()
    lastMonth = now - timedelta(days=30)
    tasks = TaskInstance.objects.filter(
        user=request.user,
        date_done__lt=now,
        date_done__gt=lastMonth,
    )
    return tasks.count()


def getStatistics(request):
    now = timezone.now()

    statistics = {
        "labels": [],
        "workHours": [],
        "tasks": [],
        "ratings": [],
    }
    statisticsSum = {"workHours": 0, "tasks": 0, "ratings": 0}

    sevenDaysAgo = timezone.now() - timedelta(days=7)

    taskQuerySet = TaskInstance.objects.filter(
        user=request.user,
        date_done__gt=sevenDaysAgo,
    )
    statisticsSum["tasks"] = taskQuerySet.count()

    ratingsQuerySet = EmployeeRating.objects.filter(
        user=request.user,
        date__gt=sevenDaysAgo,
    )
    statisticsSum["ratings"] = round(
        ratingsQuerySet.aggregate(Avg("rating"))["rating__avg"], 2
    )

    if not punchClockRecordsWereCheckedToday(request.user.id):
        run_once_day_punch_clock[request.user.id] = now.date()
        planday.authenticate()
        userEmail = User.objects.get(id=request.user.id).email
        punchClockRecordsUser[request.user.id] = (
            planday.get_user_punchclock_records_of_timespan(
                userEmail, sevenDaysAgo, now
            )
        )

    for x in range(7):
        d = now.date() - timedelta(days=x)
        statistics["labels"].insert(0, d.strftime("%m-%d"))

        tasks = taskQuerySet.filter(date_done__date=d)
        taskCount = tasks.count()
        statistics["tasks"].insert(0, taskCount)

        ratings = ratingsQuerySet.filter(date__date=d)
        rating = ratings.first().rating if ratings.count() != 0 else None
        statistics["ratings"].insert(0, rating)

        hours = 0
        for record in punchClockRecordsUser[request.user.id]:
            startDateTime = parse_datetime(record["startDateTime"])
            endDateTime = parse_datetime(record["endDateTime"])
            if startDateTime.strftime("%m-%d") == d.strftime("%m-%d"):
                diff = endDateTime - startDateTime
                hours = diff.seconds / 3600
        statistics["workHours"].insert(0, hours)

    statisticsSum["workHours"] = round(sum(statistics["workHours"]), 2)

    return (statistics, statisticsSum)


def index(request):
    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)
    myTasks = getMyTasks(request)
    ongoingShift = hasOngoingShift(request)
    tasksDoneLastMonth = getTasksDoneLastMonth(request)

    statistics, statisticsSum = getStatistics(request)
    # TODO(Rapha): figure out how to say, that there was no rating on a day. -1?
    return render(
        request,
        "index.html",
        context={
            "pageTitle": "Dashboard",
            "nextShifts": userShifts,
            "task_list": myTasks[0 : len(myTasks) if len(myTasks) <= 3 else 3],
            "tasks_done_last_month": tasksDoneLastMonth,
            "statistics_json": json.dumps(statistics, cls=DjangoJSONEncoder),
            "statistics_sum": statisticsSum,
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

import json
from datetime import datetime, timedelta

import livepopulartimes
import urllib.parse
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from lib import planday
from ratings.views import EmployeeRating
from shifts.models import Shift
from tasks.models import TaskInstance
from tasks.views import get_my_tasks
from users.models import Profile

planday = planday.Planday()
run_once_day = {}
run_once_day_punch_clock = {}
nextShifts = []
nextShiftsUser = {}
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


def getNextShiftsByUser(request):
    if not request.user.is_authenticated:
        return {}
    global nextShifts
    global nextShiftsUser
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
    ratingsAverage = ratingsQuerySet.aggregate(Avg("rating"))["rating__avg"]
    if ratingsAverage is not None:
        statisticsSum["ratings"] = round(ratingsAverage, 2)

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
        if punchClockRecordsUser:
            for record in punchClockRecordsUser[request.user.id]:
                if "startDateTime" in record and "endDateTime" in record:
                    start_date_time = parse_datetime(record["startDateTime"])
                    end_date_time = parse_datetime(record["endDateTime"])
                    if start_date_time.strftime("%m-%d") == d.strftime("%m-%d"):
                        diff = end_date_time - start_date_time
                        hours = diff.seconds / 3600
        statistics["workHours"].insert(0, hours)

    statisticsSum["workHours"] = round(sum(statistics["workHours"]), 2)

    return statistics, statisticsSum


def index(request):
    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)
    myTasks = get_my_tasks(request)
    ongoingShift = hasOngoingShift(request)
    tasksDoneLastMonth = getTasksDoneLastMonth(request)
    statistics, statisticsSum = getStatistics(request)

    user_profile = get_object_or_404(Profile, user=request.user)
    branch_address = None
    formatted_address = None
    if user_profile.branch:
        branch_address = f"{user_profile.branch.street_address}, {user_profile.branch.city}"
        print(f'branch_address: {branch_address}')
        formatted_address = f"{user_profile.branch.name} Karlsruhe"

    # Override formatted_address if provided in GET request
    if 'formatted_address' in request.GET:
        formatted_address = request.GET.get("formatted_address")

    formatted_address_str = formatted_address if formatted_address else ""

    populartimes_data = livepopulartimes.get_populartimes_by_address(formatted_address_str)
    time_spent = populartimes_data.get("time_spent", [15, 45])

    return render(
        request,
        "index.html",
        context={
            "pageTitle": "Dashboard",
            "nextShifts": userShifts[:5],
            "task_list": myTasks[:5],
            "tasks_done_last_month": tasksDoneLastMonth,
            "statistics_json": json.dumps(statistics, cls=DjangoJSONEncoder),
            "statistics": statistics,
            "statistics_sum": statisticsSum,
            "today": today,
            "ongoingShift": ongoingShift[0],
            "shiftStart": ongoingShift[1],
            "formatted_address": formatted_address_str,
            "populartimes": populartimes_data.get("populartimes", []),
            "time_spent": time_spent,
            "current_popularity": populartimes_data.get("current_popularity", []),
            "branch": user_profile.branch.name if user_profile.branch else None,
            "branch_address": branch_address,
        },
    )

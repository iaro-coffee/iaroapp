import json
import logging
from datetime import datetime, timedelta

import livepopulartimes
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from customers.models import CustomerProfile
from iaroapp.decorators import employee_required
from lib import planday
from ratings.views import EmployeeRating
from shifts.models import Shift
from tasks.models import TaskInstance
from tasks.views import get_my_tasks
from users.models import Profile

logger = logging.getLogger(__name__)


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


def get_user_profile(user):
    try:
        return Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        logger.info(f"User {user.username} does not have a profile.")
        print(f"User {user.username} does not have a profile.")
        return None


def get_customer_profile(user):
    try:
        return user.customerprofile
    except CustomerProfile.DoesNotExist:
        logger.info(f"User {user.username} does not have a customer profile.")
        print(f"User {user.username} does not have a customer profile.")
        return None


@employee_required
@login_required
def index(request: HttpRequest):
    """
    Render the dashboard page for the user with relevant data including shifts,
    tasks, and popular times data based on the user's branch address.
    """
    today = datetime.today().date()
    userShifts = getNextShiftsByUser(request)
    myTasks = get_my_tasks(request)
    ongoingShift = hasOngoingShift(request)
    tasksDoneLastMonth = getTasksDoneLastMonth(request)
    statistics, statisticsSum = getStatistics(request)
    user_profile = get_user_profile(request.user)
    customer_profile = get_customer_profile(request.user)

    # Set formatted address based on user profile and branch
    if user_profile and user_profile.branch:
        if user_profile.branch.tech_name not in ["iaro-ost", "iaro-west"]:
            formatted_address = "iaro Sophienstraße 108, Karlsruhe"
        else:
            formatted_address = (
                f"iaro {user_profile.branch.street_address}, {user_profile.branch.city}"
            )
    else:
        formatted_address = "iaro Sophienstraße 108, Karlsruhe"

    # Override formatted_address if provided in GET request
    formatted_address = request.GET.get("formatted_address", formatted_address)

    # Retrieve populartimes data
    populartimes_data = (
        livepopulartimes.get_populartimes_by_address(formatted_address)
        if formatted_address
        else {}
    )
    time_spent = populartimes_data.get("time_spent", [15, 45])
    print(formatted_address)
    context = {
        "pageTitle": "Dashboard",
        "nextShifts": userShifts[:5],
        "task_list": myTasks[:5],
        "tasks_done_last_month": tasksDoneLastMonth,
        "statistics_json": json.dumps(statistics, cls=DjangoJSONEncoder),
        "statistics": statistics,
        "statistics_sum": statisticsSum,
        "today": today,
        "ongoingShift": ongoingShift[0] if ongoingShift else None,
        "shiftStart": ongoingShift[1] if ongoingShift else None,
        "populartimes": populartimes_data.get("populartimes", []),
        "time_spent": time_spent,
        "current_popularity": populartimes_data.get("current_popularity", []),
        "formatted_address": formatted_address,
        "user_profile": user_profile,
        "customer_profile": customer_profile,
    }

    return render(request, "index.html", context=context)

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta

import livepopulartimes
import requests
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from customers.models import CustomerProfile
from employees.models import EmployeeProfile
from iaroapp.decorators import employee_required
from interactions.models import Note
from inventory.models import Branch
from lib import planday
from lib.planday import Planday
from ratings.views import EmployeeRating
from shifts.models import Shift
from tasks.models import TaskInstance
from tasks.views import get_my_tasks

logger = logging.getLogger(__name__)


def get_employee_profile(user):
    try:
        return EmployeeProfile.objects.get(user=user)
    except EmployeeProfile.DoesNotExist:
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


def sanitize_cache_key(key: str) -> str:
    """
    Sanitize cache key to ensure it's valid for memcached.
    Sha256 secure hashing algorithm.
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


@employee_required
@login_required
def get_populartimes_data(request: HttpRequest):
    user_profile = get_employee_profile(request.user)

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

    # Create a sanitized cache key based on the formatted address
    raw_cache_key = f"populartimes_data_{formatted_address}"
    cache_key = sanitize_cache_key(raw_cache_key)

    cached_data = cache.get(cache_key)

    if cached_data:
        response_data = cached_data
    else:
        # Retrieve populartimes data
        populartimes_data = (
            livepopulartimes.get_populartimes_by_address(formatted_address)
            if formatted_address
            else {}
        )
        time_spent = populartimes_data.get("time_spent", [15, 45])
        current_popularity = populartimes_data.get("current_popularity", [])
        populartimes = populartimes_data.get("populartimes", [])

        response_data = {
            "populartimes": populartimes,
            "time_spent": time_spent,
            "current_popularity": current_popularity,
        }

        cache.set(cache_key, response_data, timeout=300)

    return JsonResponse(response_data)


@employee_required
@login_required
def index(request: HttpRequest):
    """
    Render the dashboard page for the user with relevant data including shifts,
    tasks, and popular times data based on the user's branch address.
    """
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    myTasks = get_my_tasks(request)
    ongoingShift = hasOngoingShift(request)
    tasksDoneLastMonth = getTasksDoneLastMonth(request)
    statistics, statisticsSum = getStatistics(request)
    user_profile = get_employee_profile(request.user)
    customer_profile = get_customer_profile(request.user)
    current_month_year = today.strftime("%B %Y")

    # Retrieve Notes
    user_branch = user_profile.branch if user_profile else None

    combined_notes = (
        Note.objects.filter(Q(receivers=request.user) | Q(branches=user_branch))
        .distinct()
        .order_by("-timestamp")[:4]
    )

    # Get all branches and map them by departmentId
    branches_by_department_id = {
        branch.departmentId: f"{branch.street_address}, {branch.city}"
        for branch in Branch.objects.all()
    }
    # HOLIDAYS API
    holidays_cache_key = f"holidays_{today}"

    # Check if the holiday data for today is already in the cache
    holiday_data = cache.get(holidays_cache_key)
    if holiday_data is None:
        # If not, fetch the holiday data from the API
        calendarific_api_key = os.getenv("CALENDARIFIC_API_KEY")
        country = "DE"
        year = today.year
        url = f"https://calendarific.com/api/v2/holidays?&api_key={calendarific_api_key}&country={country}&year={year}"

        response = requests.get(
            url, timeout=10
        )  # Timeout 10sec to avoid potential indefinite load
        if response.status_code == 200:
            data = response.json()
            holidays = data.get("response", {}).get("holidays", [])
            # Save the data to the cache
            cache.set(
                holidays_cache_key, holidays, timeout=24 * 60 * 60
            )  # Cache for 1 day
            holiday_data = holidays
        else:
            holiday_data = []

    # Filter holidays for today and tomorrow
    today_holidays = [
        holiday
        for holiday in holiday_data
        if holiday["date"]["iso"] == today.isoformat()
    ]
    tomorrow_holidays = [
        holiday
        for holiday in holiday_data
        if holiday["date"]["iso"] == tomorrow.isoformat()
    ]

    context = {
        "pageTitle": "Dashboard",
        "task_list": myTasks[:5],
        "tasks_done_last_month": tasksDoneLastMonth,
        "statistics_json": json.dumps(statistics, cls=DjangoJSONEncoder),
        "statistics": statistics,
        "statistics_sum": statisticsSum,
        "ongoingShift": ongoingShift[0] if ongoingShift else None,
        "shiftStart": ongoingShift[1] if ongoingShift else None,
        "user_profile": user_profile,
        "customer_profile": customer_profile,
        "received_notes": combined_notes,
        "today": today,
        "tomorrow": tomorrow,
        "today_holidays": today_holidays,
        "tomorrow_holidays": tomorrow_holidays,
        "current_month_year": current_month_year,
        "branches_by_department_id": branches_by_department_id,
    }

    return render(request, "index.html", context=context)


planday = planday.Planday()
run_once_day = {}
run_once_day_punch_clock = {}
nextShifts = []
nextShiftsUser = {}
punchClockRecordsUser = {}


@login_required
@employee_required
def get_next_user_shifts(request: HttpRequest):
    """
    API view to fetch the next shifts for the current user within the current day to the end of the month.
    Cached for 24 hours unless the user requests a refresh.
    """
    try:
        user_email = request.user.email

        # Retrieve id for the current user
        employee_profile = get_object_or_404(EmployeeProfile, user=request.user)
        employee_id = employee_profile.planday_id

        # If planday_id is not available, fallback to using the email to get the ID (fetch all users)
        if not employee_id:
            employee_id = planday.get_employee_id_by_email(user_email)
            if not employee_id:
                return JsonResponse({"error": "Employee not found"}, status=404)

        cache_key = f"user_shifts_{employee_id}"
        refresh = request.GET.get("refresh", "false").lower() == "true"

        # Check if data is cached and refresh is not requested
        if not refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data)
            else:
                print("Cache miss - no shifts found")

        # If not cached or refresh is requested, fetch the shifts
        from_date = datetime.now().strftime("%Y-%m-%d")  # Define 'from' date
        end_of_month = (datetime.now() + relativedelta(day=31)).strftime(
            "%Y-%m-%d"
        )  # Define 'to' date
        shifts = planday.get_user_shifts(
            employee_id, from_date, end_of_month
        )  # Fetch shifts

        initial_shifts = shifts[:5]
        remaining_shifts = shifts[5:]

        response_data = {
            "initial_shifts": initial_shifts,
            "remaining_shifts": remaining_shifts,
        }

        # Cache the result for 24 hours
        cache.set(cache_key, response_data, timeout=60 * 60 * 24)

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"Error fetching shifts data: {str(e)}")
        return JsonResponse({"error": "Error fetching shifts data."}, status=500)


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


@login_required
@employee_required
def planday_info(request: HttpRequest):
    """
    View to fetch and display Planday portal information and departments.
    """
    planday = Planday()
    planday.authenticate()

    # Fetch portal information
    portal_info = planday.get_portal_info()

    # Fetch departments
    departments = planday.get_departments()

    # Fetch groups
    employee_groups = planday.get_employee_groups()

    context = {
        "portal_info": portal_info["data"],
        "departments": departments,
        "employee_groups": employee_groups,
    }
    print(employee_groups)
    # Render the template with the context
    return render(request, "planday.html", context)


@login_required
def get_employees_list(request):
    """
    View to fetch Employees List from Planday.
    """
    try:
        planday = Planday()
        planday.authenticate()

        employees = planday.get_employees()

        employees_list = [f"{emp['firstName']} {emp['lastName']}" for emp in employees]

        return JsonResponse({"employees": employees_list})
    except Exception:
        return JsonResponse({"error": "Unable to fetch employees list."}, status=500)

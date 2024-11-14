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

planday = planday.Planday()
run_once_day = {}
run_once_day_punch_clock = {}
nextShifts = []
nextShiftsUser = {}
punchClockRecordsUser = {}


def get_user_shifts(employee_id, from_date, to_date):
    """
    Fetch user shifts from Planday within a date range.
    """
    try:
        return planday.get_user_shifts(employee_id, from_date, to_date)
    except Exception as e:
        logger.error(f"Error fetching shifts: {str(e)}")
        return []


def get_shift_by_id(self, shift_id):
    """
    Fetch a shift by its ID.
    """
    auth_headers = self.get_auth_headers()
    endpoint = f"/scheduling/v1.0/shifts/{shift_id}"
    url = f"{self.base_url}{endpoint}"

    response = self.session.get(url, headers=auth_headers)
    response.raise_for_status()

    try:
        response_data = response.json()
        shift = response_data.get("data", {})
        return shift
    except ValueError as e:
        raise ValueError(f"Invalid JSON response from Planday API: {e}")


def initialize_employee_groups_map():
    """
    Initialize a dictionary that maps employeeGroupId to group names.
    Fetches group data from Planday.
    """
    planday.authenticate()
    employee_groups = planday.get_employee_groups()
    return {str(group["id"]): group["name"] for group in employee_groups}


def initialize_branches_by_department_id():
    """
    Initialize a dictionary that maps departmentId to both branch name and full address (street and city).
    """
    return {
        str(branch.departmentId): {
            "name": branch.name,
            "address": f"{branch.street_address}, {branch.city}",
        }
        for branch in Branch.objects.all()
    }


def enrich_shift_with_group_name(shift, employee_groups_map):
    """
    Enrich a single shift with the group name based on its employeeGroupId.
    """
    group_id = str(shift.get("employeeGroupId"))
    shift["group_name"] = employee_groups_map.get(group_id, "Unknown Group")
    return shift


def enrich_shift_with_branch_name(shift, branches_by_department_id):
    """
    Enrich a single shift with the branch name and full address based on its departmentId.
    """
    if not shift:
        print("Shift data is None.")
        return shift
    department_id = str(shift.get("departmentId"))
    branch_info = branches_by_department_id.get(
        department_id, {"name": "Unknown Branch", "address": "Unknown location"}
    )
    shift["branch_name"] = branch_info["name"]
    shift["branch_address"] = branch_info["address"]
    shift = convert_to_datetime(shift)
    return shift


def convert_to_datetime(shift):
    """
    Convert the 'startDateTime' and 'endDateTime' of a shift from string to datetime.
    """
    if "startDateTime" in shift and isinstance(shift["startDateTime"], str):
        shift["startDateTime"] = parse_datetime(shift["startDateTime"])
    if "endDateTime" in shift and isinstance(shift["endDateTime"], str):
        shift["endDateTime"] = parse_datetime(shift["endDateTime"])
    return shift


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


@login_required
@employee_required
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
    employee_id = user_profile.planday_id

    # Initialize branches_by_department_id and employee_groups_map
    branches_by_department_id = initialize_branches_by_department_id()
    employee_groups_map = initialize_employee_groups_map()

    # Authenticate and fetch shifts for the user
    planday.authenticate()
    employee_id = user_profile.planday_id
    user_shifts = get_user_shifts(employee_id, today.isoformat(), today.isoformat())

    # Check if user_shifts contains data
    if user_shifts:
        # Enrich the shift with both branch and group information
        current_shift = enrich_shift_with_group_name(
            enrich_shift_with_branch_name(user_shifts[0], branches_by_department_id),
            employee_groups_map,
        )
    else:
        current_shift = None

    # Enrich all shifts
    user_shifts = [
        enrich_shift_with_group_name(
            enrich_shift_with_branch_name(shift, branches_by_department_id),
            employee_groups_map,
        )
        for shift in user_shifts
    ]

    # Fetch punch clock records for today
    # Check if user has punched in
    # Check if shift is already punched out
    punch_clock_records = planday.get_user_punchclock_records_of_timespan(
        request.user.email, today, today
    )

    # Create a set of shift IDs that have been punched out
    punched_out_shift_ids = set()
    for record in punch_clock_records:
        shift_id = record.get("shiftId")
        if shift_id and record.get("endDateTime"):
            punched_out_shift_ids.add(shift_id)

    # Dict to store punch times for each shift ID
    punch_times_by_shift = {}

    for record in punch_clock_records:
        shift_id = record.get("shiftId")
        if shift_id:
            start_time = parse_datetime(record["startDateTime"])
            end_time = (
                parse_datetime(record["endDateTime"])
                if record.get("endDateTime")
                else None
            )
            punch_times_by_shift[shift_id] = {
                "punch_in_time": start_time,
                "punch_out_time": end_time,
            }

    # Display all shifts are done
    all_shifts_done = True

    # Include Planday shift ID
    # Annotate each shift with 'punched_out' status and punch times
    for shift in user_shifts:
        shift_id = shift.get("id")
        shift["planday_shift_id"] = shift_id
        shift["punched_out"] = shift_id in punched_out_shift_ids
        shift["punch_in_time"] = punch_times_by_shift.get(shift_id, {}).get(
            "punch_in_time"
        )
        shift["punch_out_time"] = punch_times_by_shift.get(shift_id, {}).get(
            "punch_out_time"
        )
        # check if all shifts are done
        if not shift["punched_out"]:
            all_shifts_done = False

    # Ensure `punched_in` and `punch_in_time` are correctly derived
    punched_in, punch_in_time, punch_out_time = False, None, None

    for record in punch_clock_records:
        if "endDateTime" not in record or record["endDateTime"] is None:
            # User is punched in if there's no endDateTime
            punched_in = True
            punch_in_time = parse_datetime(record["startDateTime"])
        else:
            # Capture punch-out time if available (last record should be the latest)
            punch_out_time = parse_datetime(record["endDateTime"])

    # Check for an active shift
    punched_in, active_shift = hasOngoingShift(request)

    if punched_in and active_shift:
        # Fetch current shift details from Planday using shift ID
        planday_shift = planday.get_shift_by_id(active_shift.planday_shift_id)
        if planday_shift:
            current_shift = enrich_shift_with_group_name(
                enrich_shift_with_branch_name(planday_shift, branches_by_department_id),
                employee_groups_map,
            )
            punch_in_time = active_shift.start_date
        else:
            # Handle the case where the shift details couldn't be fetched
            print("Failed to fetch shift details from Planday.")
            current_shift = None
            punch_in_time = None
    else:
        current_shift = None
        punch_in_time = None

    # Retrieve Notes
    user_branch = user_profile.branch if user_profile else None
    combined_notes = (
        Note.objects.filter(Q(receivers=request.user) | Q(branches=user_branch))
        .distinct()
        .order_by("-timestamp")[:4]
    )

    # HOLIDAYS API
    holidays_cache_key = f"holidays_{today}"
    holiday_data = cache.get(holidays_cache_key)

    if holiday_data is None:
        calendarific_api_key = os.getenv("CALENDARIFIC_API_KEY")
        country = "DE"
        year = today.year
        url = f"https://calendarific.com/api/v2/holidays?&api_key={calendarific_api_key}&country={country}&year={year}"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            holidays = data.get("response", {}).get("holidays", [])
            cache.set(holidays_cache_key, holidays, timeout=24 * 60 * 60)
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

    formatted_today = today.strftime("%A, %B %d")

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
        "formatted_today": formatted_today,
        "tomorrow": tomorrow,
        "today_holidays": today_holidays,
        "tomorrow_holidays": tomorrow_holidays,
        "current_month_year": current_month_year,
        "branches_by_department_id": branches_by_department_id,
        "user_group": (
            current_shift.get("group_name", "Unknown Group")
            if current_shift
            else "Unknown Group"
        ),
        "current_shift": current_shift,
        "user_shifts": user_shifts,
        "punched_in": punched_in,
        "punch_in_time": punch_in_time,
        "punch_out_time": punch_out_time,
        "all_shifts_done": all_shifts_done,
    }

    return render(request, "index.html", context=context)


@login_required
@employee_required
def get_next_user_shifts(request: HttpRequest):
    """
    API view to fetch the next shifts for the current user within the current day to the end of the month.
    Cached for 24 hours unless the user requests a refresh.
    """
    try:
        employee_profile = get_object_or_404(EmployeeProfile, user=request.user)
        employee_id = employee_profile.planday_id
        refresh = request.GET.get("refresh", "false").lower() == "true"

        cache_key = f"user_shifts_{employee_id}"

        # Check if data is cached and refresh is not requested
        if not refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data)

        # Initialize branches_by_department_id and employee_groups_map
        branches_by_department_id = initialize_branches_by_department_id()
        employee_groups_map = initialize_employee_groups_map()

        # Fetch shifts and enrich them with user group and branch
        from_date = datetime.now().strftime("%Y-%m-%d")
        end_of_month = (datetime.now() + relativedelta(day=31)).strftime("%Y-%m-%d")
        shifts = get_user_shifts(employee_id, from_date, end_of_month)

        # Enrich each shift with user group, branch, and group name
        enriched_shifts = [
            enrich_shift_with_group_name(
                enrich_shift_with_branch_name(shift, branches_by_department_id),
                employee_groups_map,
            )
            for shift in shifts
        ]

        # Split shifts into initial and remaining for pagination
        initial_shifts = enriched_shifts[:5]
        remaining_shifts = enriched_shifts[5:]

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
        return False, None
    try:
        active_shift = Shift.objects.filter(user=request.user, end_date=None).first()
        if active_shift:
            return True, active_shift
        else:
            return False, None
    except Shift.DoesNotExist:
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

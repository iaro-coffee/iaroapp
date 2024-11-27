import hashlib
import logging
import os
from datetime import datetime, timedelta
from threading import local

import livepopulartimes
import requests
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
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

_thread_local = local()

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
    if hasattr(_thread_local, "employee_groups_map"):
        return _thread_local.employee_groups_map
    employee_groups = planday.get_employee_groups()
    _thread_local.employee_groups_map = {
        str(group["id"]): group["name"] for group in employee_groups
    }
    return _thread_local.employee_groups_map


def initialize_branches_by_department_id():
    """
    Initialize a dictionary that maps departmentId to both branch name and full address (street and city).
    """
    if hasattr(_thread_local, "branches_by_department_id"):
        return _thread_local.branches_by_department_id
    branches = Branch.objects.all().only(
        "departmentId", "name", "street_address", "city"
    )
    _thread_local.branches_by_department_id = {
        str(branch.departmentId): {
            "name": branch.name,
            "address": f"{branch.street_address}, {branch.city}",
        }
        for branch in branches
    }
    return _thread_local.branches_by_department_id


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
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    # Initialize context with default values
    context = {
        "pageTitle": "Dashboard",
        "task_list": [],
        "tasks_done_last_month": 0,
        "statistics_json": "{}",
        "statistics": {},
        "statistics_sum": {},
        "ongoingShift": None,
        "shiftStart": None,
        "user_profile": None,
        "customer_profile": None,
        "received_notes": [],
        "today": today,
        "formatted_today": today.strftime("%A, %B %d"),
        "tomorrow": tomorrow,
        "today_holidays": [],
        "tomorrow_holidays": [],
        "current_month_year": today.strftime("%B %Y"),
        "branches_by_department_id": {},
        "user_group": "Unknown Group",
        "current_shift": None,
        "user_shifts": [],
        "punched_in": False,
        "punch_in_time": None,
        "punch_out_time": None,
        "all_shifts_done": False,
        "colleagues_at_work": [],
    }

    try:
        # Get tasks
        try:
            myTasks = get_my_tasks(request)
            context["task_list"] = myTasks[:5]
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
        #
        #     # Get ongoing shift
        #     try:
        #         ongoingShift = hasOngoingShift(request)
        #         context["ongoingShift"] = ongoingShift[0] if ongoingShift else None
        #         context["shiftStart"] = ongoingShift[1] if ongoingShift else None
        #     except Exception as e:
        #         logger.error(f"Error getting ongoing shift: {e}")
        #
        #     # Get tasks done last month
        #     try:
        #         tasksDoneLastMonth = getTasksDoneLastMonth(request)
        #         context["tasks_done_last_month"] = tasksDoneLastMonth
        #     except Exception as e:
        #         logger.error(f"Error getting tasks done last month: {e}")
        #
        #     # Get statistics
        #     try:
        #         statistics, statisticsSum = getStatistics(request)
        #         context["statistics"] = statistics
        #         context["statistics_sum"] = statisticsSum
        #         context["statistics_json"] = json.dumps(statistics, cls=DjangoJSONEncoder)
        #     except Exception as e:
        #         logger.error(f"Error getting statistics: {e}")
        #
        # Get user profile
        try:
            user_profile = get_employee_profile(request.user)
            context["user_profile"] = user_profile
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
        #
        #     # Get customer profile
        #     try:
        #         customer_profile = get_customer_profile(request.user)
        #         context["customer_profile"] = customer_profile
        #     except Exception as e:
        #         logger.error(f"Error getting customer profile: {e}")
        #
        #     # Get branches and employee groups
        #     try:
        #         branches_by_department_id = initialize_branches_by_department_id()
        #         context["branches_by_department_id"] = branches_by_department_id
        #     except Exception as e:
        #         logger.error(f"Error initializing branches: {e}")
        #         branches_by_department_id = {}
        #
        #     try:
        #         employee_groups_map = initialize_employee_groups_map()
        #     except Exception as e:
        #         logger.error(f"Error initializing employee groups map: {e}")
        #         employee_groups_map = {}
        #
        #     # Fetch shifts for the user
        #     user_shifts = []
        #     if user_profile and user_profile.planday_id:
        #         employee_id = user_profile.planday_id
        #         try:
        #             user_shifts = get_user_shifts(
        #                 employee_id, today.isoformat(), today.isoformat()
        #             )
        #             # Enrich shifts
        #             user_shifts = [
        #                 enrich_shift_with_group_name(
        #                     enrich_shift_with_branch_name(shift, branches_by_department_id),
        #                     employee_groups_map,
        #                 )
        #                 for shift in user_shifts
        #             ]
        #             context["user_shifts"] = user_shifts
        #             # Check if user_shifts contains data
        #             if user_shifts:
        #                 current_shift = user_shifts[0]
        #                 context["current_shift"] = current_shift
        #                 context["user_group"] = current_shift.get(
        #                     "group_name", "Unknown Group"
        #                 )
        #             else:
        #                 context["current_shift"] = None
        #                 context["user_group"] = "Unknown Group"
        #         except Exception as e:
        #             logger.error(f"Error fetching or processing user shifts: {e}")
        #             context["user_shifts"] = []
        #             context["current_shift"] = None
        #             context["user_group"] = "Unknown Group"
        #     else:
        #         logger.warning("User profile or planday_id not found.")
        #         context["user_shifts"] = []
        #         context["current_shift"] = None
        #         context["user_group"] = "Unknown Group"
        #
        #     # Sync shifts
        #     try:
        #         sync_shifts(request.user)
        #     except Exception as e:
        #         logger.error(f"Error syncing shifts: {e}")
        #
        #     # Fetch punch clock records for today
        #     try:
        #         punch_clock_records = planday.get_user_punchclock_records_of_timespan(
        #             request.user.email, today, today
        #         )
        #         # Process punch clock records
        #         # Dict to store punch times for each shift ID
        #         punch_times_by_shift = {}
        #         punched_out_shift_ids = set()
        #
        #         for record in punch_clock_records:
        #             shift_id = record.get("shiftId")
        #             start_time = parse_datetime(record.get("startDateTime"))
        #             end_time = (
        #                 parse_datetime(record.get("endDateTime"))
        #                 if record.get("endDateTime")
        #                 else None
        #             )
        #
        #             if shift_id:
        #                 punch_times_by_shift[shift_id] = {
        #                     "punch_in_time": start_time,
        #                     "punch_out_time": end_time,
        #                 }
        #                 if end_time:
        #                     punched_out_shift_ids.add(shift_id)
        #
        #         # Annotate shifts with punch times and statuses
        #         for shift in user_shifts:
        #             shift_id = shift.get("id")
        #             shift["planday_shift_id"] = shift_id
        #             shift["punched_out"] = shift_id in punched_out_shift_ids
        #             shift["punch_in_time"] = punch_times_by_shift.get(shift_id, {}).get(
        #                 "punch_in_time"
        #             )
        #             shift["punch_out_time"] = punch_times_by_shift.get(shift_id, {}).get(
        #                 "punch_out_time"
        #             )
        #
        #         # Determine if all shifts are done
        #         if user_shifts:
        #             all_shifts_done = all(
        #                 shift.get("punched_out", False) for shift in user_shifts
        #             )
        #         else:
        #             all_shifts_done = False
        #         context["all_shifts_done"] = all_shifts_done
        #
        #         # Check for an active shift in Planday
        #         active_shift = None
        #         punched_in = False
        #         punch_in_time = None
        #         punch_out_time = None
        #
        #         for record in punch_clock_records:
        #             if record.get("endDateTime") is None:  # Active shift
        #                 punched_in = True
        #                 punch_in_time = parse_datetime(record["startDateTime"])
        #                 shift_id = record.get("shiftId")
        #                 # Only fetch shift details if shift_id is not None
        #                 if shift_id:
        #                     active_shift = next(
        #                         (shift for shift in user_shifts if shift["id"] == shift_id),
        #                         None,
        #                     )
        #                     if not active_shift:
        #                         # As a fallback, fetch the shift by ID
        #                         try:
        #                             active_shift = planday.get_shift_by_id(shift_id)
        #                             if active_shift:
        #                                 active_shift = enrich_shift_with_group_name(
        #                                     enrich_shift_with_branch_name(
        #                                         active_shift, branches_by_department_id
        #                                     ),
        #                                     employee_groups_map,
        #                                 )
        #                         except Exception as e:
        #                             logger.error(f"Error fetching shift by ID: {e}")
        #                             active_shift = None
        #                 break
        #
        #         # If there's an active shift, override the current shift
        #         if active_shift:
        #             context["current_shift"] = active_shift
        #
        #         context["punched_in"] = punched_in
        #         context["punch_in_time"] = punch_in_time
        #         context["punch_out_time"] = punch_out_time
        #
        #     except Exception as e:
        #         logger.error(f"Error processing punch clock records: {e}")
        #         context["punched_in"] = False
        #         context["punch_in_time"] = None
        #         context["punch_out_time"] = None
        #         context["all_shifts_done"] = False

        # Retrieve Notes
        try:
            user_branch = user_profile.branch if user_profile else None
            combined_notes = (
                Note.objects.select_related("sender")
                .filter(Q(receivers=request.user) | Q(branches=user_branch))
                .distinct()
                .order_by("-timestamp")[:4]
            )
            context["received_notes"] = combined_notes
        except Exception as e:
            logger.error(f"Error fetching notes: {e}")
            context["received_notes"] = []

        # HOLIDAYS API
        try:
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
            else:
                holiday_data = holiday_data

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
            context["today_holidays"] = today_holidays
            context["tomorrow_holidays"] = tomorrow_holidays
        except Exception as e:
            logger.error(f"Error fetching holidays: {e}")
            context["today_holidays"] = []
            context["tomorrow_holidays"] = []

        # Get colleagues at work
        # try:
        #     colleagues_at_work = get_colleagues_at_work(user_profile, today)
        #     context["colleagues_at_work"] = colleagues_at_work
        # except Exception as e:
        #     logger.error(f"Error fetching colleagues at work: {e}")
        #     context["colleagues_at_work"] = []

    except Exception as e:
        logger.error(f"An unexpected error occurred in index view: {e}")
        context["error_message"] = (
            "An unexpected error occurred. Please send a report to igor@iaro.co"
        )

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


def parse_datetime_to_aware(date_str):
    dt = parse_datetime(date_str)
    if dt is not None and dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    return dt


def getStatistics(request):
    now = timezone.now()

    statistics = {
        "labels": [],
        "workHours": [],
        "tasks": [],
        "ratings": [],
    }
    statisticsSum = {"workHours": 0, "tasks": 0, "ratings": 0}

    sevenDaysAgo = now - timedelta(days=7)

    # Fetch and annotate tasks per day
    taskQuerySet = TaskInstance.objects.filter(
        user=request.user,
        date_done__gte=sevenDaysAgo,
        date_done__lte=now,
    )
    statisticsSum["tasks"] = taskQuerySet.count()

    tasks_per_day = (
        taskQuerySet.annotate(day=TruncDate("date_done"))
        .values("day")
        .annotate(count=Count("id"))
    )
    tasks_per_day_dict = {item["day"]: item["count"] for item in tasks_per_day}

    # Fetch and annotate ratings per day
    ratingsQuerySet = EmployeeRating.objects.filter(
        user=request.user,
        date__gte=sevenDaysAgo,
        date__lte=now,
    )
    ratingsAverage = ratingsQuerySet.aggregate(Avg("rating"))["rating__avg"]
    if ratingsAverage is not None:
        statisticsSum["ratings"] = round(ratingsAverage, 2)

    ratings_per_day = (
        ratingsQuerySet.annotate(day=TruncDate("date"))
        .values("day")
        .annotate(avg_rating=Avg("rating"))
    )
    ratings_per_day_dict = {item["day"]: item["avg_rating"] for item in ratings_per_day}

    # Fetch punch clock records for the past 7 days
    userEmail = request.user.email
    punch_clock_records = planday.get_user_punchclock_records_of_timespan(
        userEmail, sevenDaysAgo.date(), now.date()
    )

    # Organize punch clock records by date
    punch_clock_records_by_date = {}
    for record in punch_clock_records:
        start_date_time = parse_datetime_to_aware(record["startDateTime"])
        end_date_time = (
            parse_datetime_to_aware(record["endDateTime"])
            if record.get("endDateTime")
            else now
        )
        date_str = start_date_time.strftime("%Y-%m-%d")
        duration = (end_date_time - start_date_time).total_seconds() / 3600
        punch_clock_records_by_date.setdefault(date_str, 0)
        punch_clock_records_by_date[date_str] += duration

    for x in range(7):
        d = (now - timedelta(days=x)).date()
        date_str = d.strftime("%Y-%m-%d")
        statistics["labels"].insert(0, d.strftime("%m-%d"))

        # Tasks
        task_count = tasks_per_day_dict.get(d, 0)
        statistics["tasks"].insert(0, task_count)

        # Ratings
        rating = ratings_per_day_dict.get(d, 0)
        statistics["ratings"].insert(0, rating if rating is not None else 0)

        # Work Hours
        hours = punch_clock_records_by_date.get(date_str, 0)
        statistics["workHours"].insert(0, round(hours, 2))

    statisticsSum["workHours"] = round(sum(statistics["workHours"]), 2)

    return statistics, statisticsSum


@login_required
@employee_required
def planday_info(request: HttpRequest):
    """
    View to fetch and display Planday portal information and departments.
    """
    planday = Planday()

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

        employees = planday.get_employees()

        employees_list = [f"{emp['firstName']} {emp['lastName']}" for emp in employees]

        return JsonResponse({"employees": employees_list})
    except Exception:
        return JsonResponse({"error": "Unable to fetch employees list."}, status=500)


def get_colleagues_at_work(user_profile, today):
    # Ensure the user has a branch assigned
    if not user_profile or not user_profile.branch:
        print("User does not have a branch assigned.")
        return []

    # Get the department ID (departmentId) of the user's branch
    user_department_id = str(user_profile.branch.departmentId)

    # Get all EmployeeProfiles in the same department, excluding the current user
    colleagues_profiles = EmployeeProfile.objects.filter(
        branch__departmentId=user_department_id
    ).exclude(user=user_profile.user)

    # Build a mapping from planday_id to colleague profile
    colleagues_by_planday_id = {
        str(colleague.planday_id): colleague
        for colleague in colleagues_profiles
        if colleague.planday_id and str(colleague.planday_id).isdigit()
    }

    colleagues_planday_ids = list(colleagues_by_planday_id.keys())

    if not colleagues_planday_ids:
        print("No colleagues with valid Planday IDs found.")
        return []

    # Fetch shifts for all colleagues on the current day
    from_date = today.isoformat()
    to_date = today.isoformat()

    try:
        shifts = planday.get_user_shifts_bulk(
            colleagues_planday_ids, from_date, to_date
        )
    except Exception as e:
        print(f"Error fetching shifts for colleagues: {e}")
        return []  # Return empty list if there's an error

    branches_by_department_id = initialize_branches_by_department_id()
    employee_groups_map = initialize_employee_groups_map()

    # For each shift, get the colleague and build data
    colleagues_at_work = []
    for shift in shifts:
        employee_id = str(shift.get("employeeId"))
        colleague = colleagues_by_planday_id.get(employee_id)
        if colleague:
            shift = enrich_shift_with_group_name(
                enrich_shift_with_branch_name(shift, branches_by_department_id),
                employee_groups_map,
            )
            colleague_data = {
                "colleague": colleague,
                "shift": shift,
                "department_name": (
                    colleague.branch.name if colleague.branch else "Unknown Department"
                ),
            }
            colleagues_at_work.append(colleague_data)
        else:
            print(f"No colleague found for employee ID {employee_id}")

    return colleagues_at_work

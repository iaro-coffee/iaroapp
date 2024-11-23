import json

from dateutil.parser import parse as parse_datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.timezone import get_current_timezone, make_aware, now
from django.views import View

from lib.planday import Planday
from ratings.models import EmployeeRating
from shifts.models import Shift

planday = Planday()


def parse_datetime_to_aware(date_str):
    dt = parse_datetime(date_str)
    if dt.tzinfo is None:
        dt = make_aware(dt, get_current_timezone())
    return dt


def get_active_shift(user):
    """
    Retrieves the active shift for the user, checking both the local DB and Planday.
    If the shift is only in Planday, it will be imported into the local DB.
    """
    active_shift = Shift.objects.filter(user=user, end_date=None).first()
    if active_shift:
        return active_shift
    else:
        # Check Planday for an active shift
        current_time = now()

        punch_clock_records = planday.get_user_punchclock_records_of_timespan(
            user.email, current_time.date(), current_time.date()
        )
        for record in punch_clock_records:
            if record.get("endDateTime") is None:
                # Active shift found
                planday_shift_id = record.get("shiftId")
                start_time = parse_datetime_to_aware(record["startDateTime"])
                # Create the shift in the local DB
                active_shift = Shift.objects.create(
                    user=user,
                    planday_shift_id=planday_shift_id,
                    start_date=start_time,
                    note="Imported from Planday",
                )
                break
        return active_shift


def sync_shifts(user):
    """
    Synchronizes shifts in the local DB with Planday shifts for the user.
    Updates shifts that have been ended in Planday but not in the local DB.
    Also handles shifts that were reset (deleted) in Planday.
    """
    current_time = now()
    # Get punch clock records for today
    punch_clock_records = planday.get_user_punchclock_records_of_timespan(
        user.email, current_time.date(), current_time.date()
    )
    # Build a set of shift IDs from Planday
    planday_shift_ids = set()
    for record in punch_clock_records:
        shift_id = record.get("shiftId")
        start_time = parse_datetime_to_aware(record.get("startDateTime"))
        end_time = (
            parse_datetime_to_aware(record.get("endDateTime"))
            if record.get("endDateTime")
            else None
        )
        planday_shift_ids.add(shift_id)
        # Try to find the shift in the local DB
        shift, created = Shift.objects.get_or_create(
            user=user,
            planday_shift_id=shift_id,
            defaults={
                "start_date": start_time,
                "end_date": end_time,
                "note": "Imported from Planday",
            },
        )
        if not created:
            # Update the shift if end_date is None and Planday shows it has ended
            if shift.end_date is None and end_time:
                shift.end_date = end_time
                shift.save()
    # Handle shifts in local DB that are not in Planday
    local_shifts = Shift.objects.filter(user=user, start_date__date=current_time.date())
    for shift in local_shifts:
        if shift.planday_shift_id not in planday_shift_ids:
            # Shift is in local DB but not in Planday
            shift.delete()


@method_decorator(login_required, name="dispatch")
class ShiftManagementView(View):
    def post(self, request):
        """
        Handles Punch-In and Punch-Out based on user shift status.
        """
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_id = int(data.get("user_id"))
            action = data.get("action")
            rating = data.get("rating", None)
            comment = data.get("comment", "")
            confirm_reset = data.get("confirm_reset", False)
            shift_id = data.get("shift_id", None)

            user = get_object_or_404(User, id=user_id)
            email = user.email
            current_time = now()  # Timezone-aware datetime

            # Synchronize shifts before proceeding
            sync_shifts(user)

            if action == "punch_in":
                # Check if user is already punched in
                active_shift = get_active_shift(user)
                if active_shift:
                    return JsonResponse(
                        {"status": "error", "message": "You are already punched in."},
                        status=400,
                    )

                if not shift_id:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Shift ID is required for punch-in.",
                        },
                        status=400,
                    )

                # Proceed to punch in
                status = planday.punch_in_by_email(email, shift_id, comment)
                if status == 200:
                    Shift.objects.create(
                        user=user,
                        start_date=current_time,
                        planday_shift_id=int(shift_id),
                        note=comment,
                    )
                    return JsonResponse(
                        {"status": "success", "message": "Punched In successfully."},
                        status=200,
                    )
                else:
                    return JsonResponse(
                        {"status": "error", "message": "Failed to Punch In."},
                        status=status,
                    )

            elif action == "punch_out":
                # Get the active shift
                active_shift = get_active_shift(user)
                if not active_shift:
                    return JsonResponse(
                        {"status": "error", "message": "No active shift found."},
                        status=400,
                    )

                if shift_id and int(shift_id) != active_shift.planday_shift_id:
                    return JsonResponse(
                        {"status": "error", "message": "Shift ID mismatch."}, status=400
                    )

                # Check if reset confirmation is needed
                if not confirm_reset:
                    shift_duration = (
                        current_time - active_shift.start_date
                    ).total_seconds()
                    if shift_duration < 120:
                        # Shift is less than 2 minutes
                        return JsonResponse(
                            {
                                "status": "warning",
                                "message": "Shift duration is less than 2 minutes. Do you want to reset the shift?",
                                "requires_confirmation": True,
                            },
                            status=409,
                        )

                response = planday.punch_out_by_email(
                    email, active_shift.planday_shift_id, comment=comment
                )
                if response is None:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Punch-Out failed. Invalid employee.",
                        },
                        status=500,
                    )
                status = response.status_code

                if confirm_reset:
                    active_shift.delete()
                    return JsonResponse(
                        {"status": "success", "message": "Shift reset successfully."},
                        status=200,
                    )

                if status == 200:
                    if rating:
                        rating_obj = EmployeeRating.objects.create(
                            user=user, rating=rating, date=current_time, comment=comment
                        )
                        active_shift.rating = rating_obj
                    active_shift.end_date = current_time
                    active_shift.save()
                    return JsonResponse(
                        {"status": "success", "message": "Punched Out successfully."},
                        status=200,
                    )
                else:
                    return JsonResponse(
                        {"status": "error", "message": "Punch-Out failed."},
                        status=status,
                    )

            else:
                return JsonResponse(
                    {"status": "error", "message": "Invalid action."}, status=400
                )

        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Error in ShiftManagementView: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

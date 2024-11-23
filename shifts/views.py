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

            planday.authenticate()

            # Fetch active shift from the local DB
            active_shift = Shift.objects.filter(user=user, end_date=None).first()

            # Check Planday for an active shift if none exists in the local DB
            if not active_shift and action == "punch_out":
                punch_clock_records = planday.get_user_punchclock_records_of_timespan(
                    email, current_time.date(), current_time.date()
                )
                for record in punch_clock_records:
                    if record.get("endDateTime") is None:  # Active shift found
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

            if action == "punch_in":
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
                if not active_shift:
                    return JsonResponse(
                        {"status": "error", "message": "No active shift found."},
                        status=400,
                    )

                if shift_id and int(shift_id) != active_shift.planday_shift_id:
                    return JsonResponse(
                        {"status": "error", "message": "Shift ID mismatch."}, status=400
                    )

                if not confirm_reset:
                    shift_duration = (
                        current_time - active_shift.start_date
                    ).total_seconds()
                    if shift_duration < 120:
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

            return JsonResponse(
                {"status": "error", "message": "Invalid action."}, status=400
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Convert naive datetime to timezone-aware
def parse_datetime_to_aware(date_str):
    dt = parse_datetime(date_str)
    if dt.tzinfo is None:  # Check if the datetime is naive
        dt = make_aware(dt, get_current_timezone())
    return dt

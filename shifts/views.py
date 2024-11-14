import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.timezone import now
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
            shift_id = data.get("shift_id", None)  # Get shift ID from request

            # Add a print statement to verify the comment
            print(f"Received comment: {comment}")

            user = get_object_or_404(User, id=user_id)
            email = user.email
            current_time = now()

            planday.authenticate()

            # Fetch the active shift for the user
            active_shift = Shift.objects.filter(user=user, end_date=None).first()

            if action == "punch_in":
                # Punch-In logic
                if active_shift:
                    # If a shift already exists, invalid operation
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
                    # Create a shift record in the DB with the Planday shift ID
                    Shift.objects.create(
                        user=user,
                        start_date=current_time,
                        planday_shift_id=int(shift_id),
                        note=comment,  # Save the note
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
                # Punch-Out logic with rating
                if not active_shift:
                    # If no active shift, invalid operation
                    return JsonResponse(
                        {"status": "error", "message": "No active shift found."},
                        status=400,
                    )

                if shift_id and int(shift_id) != active_shift.planday_shift_id:
                    # The shift ID provided does not match the active shift
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
                    # If reset was confirmed, delete the shift record
                    active_shift.delete()
                    return JsonResponse(
                        {"status": "success", "message": "Shift reset successfully."},
                        status=200,
                    )

                if status == 200:
                    # Successful punch-out
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
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

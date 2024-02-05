from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from ratings.models import EmployeeRating
from django.http import HttpResponse
import json
import datetime
from lib import planday

from shifts.models import Shift

planday = planday.Planday()

@login_required
def index(request):
    if request.method == 'POST':
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, value in form_data.items():
            star = value.get('star')
            user = User.objects.get(id=user_id)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            shifts = Shift.objects.filter(user=request.user, end_date=None)
            print(user.email)
            planday.authenticate()
            if not shifts:  # if no open shift exists, create one
                status = planday.punch_in_by_email(user.email)
                if status == 200:
                    Shift.objects.create(user=user, start_date=date)
                else:
                    return HttpResponse(status=status)
            else:  # else close shift with rating
                status = planday.punch_out_by_email(user.email)
                if status == 200:
                    rating = EmployeeRating.objects.create(user=user, rating=star, date=date)
                    shifts.update(end_date=date, rating=rating)
                else:
                    return HttpResponse(status=status)
        return HttpResponse(status=200)
    return
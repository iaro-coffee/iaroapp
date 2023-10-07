from math import floor

from django.contrib.auth.models import User
from django.db.models import Sum
from lib.planday import Planday
import datetime
from tips.models import AssignedTip, Tip

def assignTips():
    # run: python manage.py crontab add
    # check them with: python manage.py crontab show

    print("assigning tips...")

    planday = Planday()
    planday.authenticate()
    today_shifts = planday.get_shifts_today_users()
    bar_times = {}
    kitchen_times = {}

    # 1. get minutes of users from todays shift
    for user, shift in today_shifts.items():
        user_obj = User.objects.filter(email=user).distinct().values('id', 'email')
        try:
            user = user_obj[0]
            start = datetime.datetime.strptime(shift['startDateTime'], '%Y-%m-%dT%H:%M:%S.%f')
            end = datetime.datetime.strptime(shift['endDateTime'], '%Y-%m-%dT%H:%M:%S.%f')
            minutes = floor((end - start).total_seconds() / 60)
            groups = planday.get_user_groups(shift['employeeId'])
            print(groups)
            if 272480 in groups or 275780 in groups:
                bar_times[user['id']] = minutes
            elif 274170 in groups:
                kitchen_times[user['id']] = minutes
        except:
            print("user " + str(user))
            print('user from planday does not exist in django')

    # 2. Calculate AssignedTips
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    tips_sum = Tip.objects.filter(date__range=(today_min, today_max)).aggregate(Sum('amount'))['amount__sum']
    kitchen_tips_sum = floor((0.2*tips_sum) * 100)/100.0
    bar_tips_sum = floor((tips_sum - kitchen_tips_sum) * 100)/100.0

    bar_times_sum = sum(bar_times.values())
    kitchen_times_sum = sum(kitchen_times.values())

    for user, minutes in bar_times.items():
        user_amount = floor((bar_tips_sum / bar_times_sum * minutes) * 100)/100.0
        AssignedTip.objects.create(user=User.objects.get(id=user), amount=user_amount, date=datetime.datetime.now())

    for user, minutes in kitchen_times.items():
        user_amount = floor((kitchen_tips_sum / kitchen_times_sum * minutes) * 100)/100.0
        AssignedTip.objects.create(user=User.objects.get(id=user), amount=user_amount, date=datetime.datetime.now())


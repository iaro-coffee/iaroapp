from math import floor

from django.contrib.auth.models import User
from django.db.models import Sum
from lib.planday import Planday
import datetime
from tips.models import AssignedTip, Tip

def assignTips():
    # run: python manage.py crontab add
    # check them with: python manage.py crontab show

    today = datetime.datetime.today()
    for i in range(1, today.day + 1):
        day = datetime.datetime.today().replace(day=i)

        print("assigning tips for day " + str(day))

        planday = Planday()
        planday.authenticate()
        shifts = planday.get_user_shifts_of_day(day)
        bar_times = {}
        kitchen_times = {}

        # 1. get minutes of users from todays shift
        for user, shift in shifts.items():
            user_obj = User.objects.filter(email=user).distinct().values('id', 'email')
            try:
                user_unwrapped = user_obj[0]
                print('reading shift of user ' + str(user_unwrapped))
                print(shift)
                if 'startDateTime' in shift and 'endDateTime' in shift:
                    startDateTime = shift['startDateTime']
                    endDateTime = shift['endDateTime']
                    start = datetime.datetime.strptime(startDateTime, '%Y-%m-%dT%H:%M:%S.%f')
                    end = datetime.datetime.strptime(endDateTime, '%Y-%m-%dT%H:%M:%S.%f')
                else:
                    startDateTime = shift['shiftStartDateTime']
                    endDateTime = shift['shiftEndDateTime']
                    start = datetime.datetime.strptime(startDateTime, '%Y-%m-%dT%H:%M')
                    end = datetime.datetime.strptime(endDateTime, '%Y-%m-%dT%H:%M')
                print('shift: ' + str(start) + ' - ' + str(end))

                # if end is later than 18:30, cap it
                chop = day.replace(hour=18, minute=30)
                if end > chop:
                    end = chop
                minutes = floor((end - start).total_seconds() / 60)
                print('user minutes: ' + str(minutes))
                groups = planday.get_user_groups(shift['employeeId'])

                if 272480 in groups or 275780 in groups:
                    bar_times[user_unwrapped['id']] = minutes
                elif 274170 in groups:
                    kitchen_times[user_unwrapped['id']] = minutes
            except:
                print("user " + str(user))
                print('user from planday does not exist in django')

        # 2. Calculate AssignedTips
        day_min = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_max = day.replace(hour=23, minute=59, second=59)
        tips_sum = Tip.objects.filter(date__range=(day_min, day_max)).aggregate(Sum('amount'))['amount__sum']
        if tips_sum:
            kitchen_tips_sum = floor((0.2*tips_sum) * 100)/100.0
            bar_tips_sum = floor((tips_sum - kitchen_tips_sum) * 100)/100.0

            bar_times_sum = sum(bar_times.values())
            kitchen_times_sum = sum(kitchen_times.values())

            print('bar_times_sum ' + str(bar_times_sum))
            print('kitchen_times_sum ' + str(kitchen_times_sum))

            for user, minutes in bar_times.items():
                user_amount = floor((bar_tips_sum / bar_times_sum * minutes) * 100)/100.0
                print('create tip for user ' + str(user) + ' with amount ' + str(user_amount))
                AssignedTip.objects.update_or_create(user=User.objects.get(id=user), date=day.date(), defaults=dict(amount=user_amount, minutes=minutes),)

            for user, minutes in kitchen_times.items():
                user_amount = floor((kitchen_tips_sum / kitchen_times_sum * minutes) * 100)/100.0
                print('create tip for user ' + str(user) + ' with amount ' + str(user_amount))
                AssignedTip.objects.update_or_create(user=User.objects.get(id=user), date=day.date(), defaults=dict(amount=user_amount, minutes=minutes),)


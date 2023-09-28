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
            start = datetime.datetime.strptime(shift['startDateTime'], '%Y-%m-%dT%H:%M')
            end = datetime.datetime.strptime(shift['endDateTime'], '%Y-%m-%dT%H:%M')
            minutes = (end - start).total_seconds() / 60
            if shift['employeeGroupId'] == 272480 or shift['employeeGroupId'] == 275780:
                bar_times[user['id']] = minutes
            elif shift['employeeGroupId'] == 274170:
                kitchen_times[user['id']] = minutes
        except:
            print('user from planday does not exist in django')

    # 2. Calculate AssignedTips
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    tips_sum = Tip.objects.filter(date__range=(today_min, today_max)).aggregate(Sum('amount'))['amount__sum']
    kitchen_tips_sum = round(0.2*tips_sum,2)
    bar_tips_sum = round(tips_sum - kitchen_tips_sum,2)

    bar_times_sum = sum(bar_times.values())
    kitchen_times_sum = sum(kitchen_times.values())

    for user, minutes in bar_times.items():
        user_amount = round(bar_tips_sum / bar_times_sum * minutes, 2)
        AssignedTip.objects.create(user=User.objects.get(id=user), amount=user_amount, date=datetime.datetime.now())

    for user, minutes in kitchen_times.items():
        user_amount = round(kitchen_tips_sum / kitchen_times_sum * minutes, 2)
        AssignedTip.objects.create(user=User.objects.get(id=user), amount=user_amount, date=datetime.datetime.now())


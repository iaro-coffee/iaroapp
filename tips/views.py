from django.contrib.auth.models import User
from django.shortcuts import render

from iaroapp.cron import assignTips
from ratings.models import EmployeeRating
# Create your views here.

from .models import Tip

from django.contrib.auth import get_user_model
from django.http import HttpResponse
import json
import datetime
from lib import planday

planday = planday.Planday()
run_once_day = ""
shift_today_users = []

# Tip input page
def index(request):
    if request.method == 'POST':
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, value in form_data.items():
            amount = value['tip']
            star = value['star']
            user = User.objects.get(id=user_id)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # add tip
            if amount:
                amount = amount.replace(',','.')
                amount = float(amount)
                # Only add tips to database which have a value
                if amount > 0 or amount < 0:
                    Tip.objects.create(user=user, amount=amount, date=date)

            # add star
            EmployeeRating.objects.create(user=user, rating=star, date=date)
        return HttpResponse(200)

    return render(
        request,
        'tips.html',
        context={
        },
    )

from django.forms.models import model_to_dict
from django.contrib.auth.decorators import user_passes_test

def strip_day(someDate):
    return someDate.replace(day=1)

def check_admin(user):
   return user.is_superuser

@user_passes_test(check_admin)
def evaluation(request):

    User = get_user_model()
    users = User.objects.all()

    # Calculate chart
    chartLabels = []
    dayNow = datetime.datetime.now()
    for lastDays in range(0,7):
        lastDay = dayNow - datetime.timedelta(days=6-lastDays)
        chartLabels.append(lastDay.strftime("%A"))
    chartValues = []
    allTips = Tip.objects.all()
    for lastDays in range(0,7):
        thisDay = dayNow - datetime.timedelta(days=6-lastDays)
        thisDay = thisDay.strftime("%Y-%m-%d")
        amountToday = 0
        for tip in allTips:
            tip = model_to_dict(tip)
            tipDate = tip['date'].date()
            if str(tipDate) == str(thisDay):
                amountToday += float(tip['amount'])
        chartValues.append(amountToday)

    # Calculate evaluation
    evaluation = []
    result = Tip.objects.all()
    for user in users:
        userDict = {}
        userDict['user_id'] = user.id
        userDict['user_name'] = user.get_username()
        userDict['user_firstname'] = user.first_name
        userDict['user_lastname'] = user.last_name
        userDict['amountToday'] = 0
        userDict['amountThisMonth'] = 0
        userDict['amountLastMonth'] = 0
        for tip in result:
            tip = model_to_dict(tip)
            if user.id == tip['user']:

                tipDate = tip['date'].date()
                today = datetime.datetime.today().date()
                first = today.replace(day=1)
                lastMonth = first - datetime.timedelta(days=1)

                if today == tipDate:
                    userDict['amountToday'] += float(tip['amount'])

                if strip_day(today) == strip_day(tipDate):
                    userDict['amountThisMonth'] += float(tip['amount'])

                if strip_day(lastMonth) == strip_day(tipDate):
                    userDict['amountLastMonth'] += float(tip['amount'])
        evaluation.append(userDict)

    # Calculate evaluation
    latestTips = []
    result = Tip.objects.all()
    for tip in result:
        entry = {}
        tip = model_to_dict(tip)
        if tip['amount'] > 0 or tip['amount'] < 0:
            entry['amount'] = tip['amount']
            entry['date'] = tip['date'].strftime("%d.%m.%Y %H:%M") + " Uhr"
            user = User.objects.get(id=int(tip['user']))
            if (user.first_name and user.last_name):
                username = user.first_name + " " + user.last_name
            else: 
                username = user
            entry['user'] = username
            latestTips.append(entry)

    # Reverse list, having newest tips on top
    latestTips = list(reversed(latestTips))
    # Limit recent tips list to 20 entries
    latestTips = latestTips[:20]

    return render(
        request,
        'evaluation.html',
        context={
            'users': users,
            'evaluation': evaluation,
            'chartLabels': chartLabels,
            'chartValues': chartValues,
            'latestTips': latestTips
        },
    )


from django.views import generic

class TipsListView(generic.ListView):
    """Generic class-based view for a list of tips."""
    model = Tip
    paginate_by = 10


class TipsDetailView(generic.DetailView):
    """Generic class-based detail view for a task."""
    model = Tip

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin

# Classes created for the forms challenge
class TipsCreate(PermissionRequiredMixin, CreateView):
    model = Tip
    fields = ['title']

class TipsUpdate(PermissionRequiredMixin, UpdateView):
    model = Tip
    fields = ['title']

class TipsDelete(PermissionRequiredMixin, DeleteView):
    model = Tip
    success_url = reverse_lazy('tip')
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Tip

from django.contrib.auth import get_user_model
from tips.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
from django.http.multipartparser import MultiPartParser
from django.utils import timezone
import json
import datetime
from lib import planday

planday = planday.Planday()
run_once_day = ""
shift_today_users = []

# Tip input page
def index(request):

    today = str(datetime.datetime.now().strftime("%Y-%m-%d"))
    global run_once_day
    global shift_today_users

    if run_once_day != today:
        planday.authenticate()
        shift_today_users = planday.get_shifts_today_users()
        run_once_day = today

    User = get_user_model()
    users = User.objects.all()

    if request.method == 'POST':
        form = Form(request.POST)

        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, amount in form_data.items():
            user = User.objects.get(id=user_id)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if amount:
                amount = amount.replace(',','.')
                amount = float(amount)
                # Only add tips to database which have a value
                if amount > 0 or amount < 0:
                    Tip.objects.create(user=user, amount=amount, date=date)
        return HttpResponse(200)

    else:
            
        today = datetime.datetime.today().date()
        isSubmittedToday = False
        users = User.objects.filter(
            email__in=shift_today_users)
        dt = datetime.datetime.now().strftime("%Y-%m-%d")
        shifts = planday.get_upcoming_shifts(dt,dt)
        
        if 'tip' in request.GET:
            now = datetime.datetime.today().hour + 2
            complete_tip = float(request.GET['tip'])
            kitchen_tip = 0.0
            if now in range(12, 15, 1):
                kitchen_tip = round((complete_tip * 0.2), 2)
                counter_tip = complete_tip - kitchen_tip
            else:
                counter_tip = complete_tip
            
            kitchenId = 274170
            baristaId = 272480
            now = datetime.datetime.now()
            kitchenStaff = []
            baristaStaff = []
            for shift in shifts:
                start = datetime.datetime.strptime(shift['start'], '%Y-%m-%dT%H:%M')
                end = datetime.datetime.strptime(shift['end'], '%Y-%m-%dT%H:%M')
                if start < now and end > now:
                    if shift['groupId'] == kitchenId:
                        kitchenStaff.append(shift['employee'])
                    elif shift['groupId'] == baristaId:
                        baristaStaff.append(shift['employee'])
            tipMap = {}
            for employee in kitchenStaff:
                tipMap[employee] = kitchen_tip/kitchenStaff.__len__()
            for employee in baristaStaff:
                tipMap[employee] = counter_tip/baristaStaff.__len__()
            for user in users:
                if user.email in tipMap:
                    user.tip = tipMap[user.email]
                else:
                    user.tip = 0.0
                    
        for tip in Tip.objects.all():
            tip = model_to_dict(tip)
            if tip['date'].date() == today:
                isSubmittedToday = True
                break

        form = Form()
        context = {
            'isSubmittedToday': isSubmittedToday,
            'users': users,
            'form': form,
        }
    return render(
        request,
        'tips.html',
        context,
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
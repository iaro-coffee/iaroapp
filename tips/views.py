from math import floor

from django.contrib.auth.models import User
from django.shortcuts import render

from iaroapp.cron import assignTips
from ratings.models import EmployeeRating
# Create your views here.

from .models import Tip, AssignedTip

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
    assignedTips = AssignedTip.objects.filter(date__month__gte=datetime.datetime.now().strftime("%m"))
    tipsSum = 0
    for tip in assignedTips:
        tipsSum += model_to_dict(tip)['amount']
    items = []
    for i in range(1, 32):
        tips = []
        sumHours = 0
        sumAmount = 0
        for tip in assignedTips:
            if tip.date == datetime.datetime.now().replace(day=i).date():
                tips.append({'name': tip.user.username, 'hours': floor((tip.minutes / 60)*100)/100.0, 'amount': tip.amount})
                sumHours += tip.minutes/60
                sumAmount += tip.amount
        if tips:
            items.insert(0,{'id': i, 'date': datetime.datetime.now().replace(day=i).date(), 'assignedTips': tips, 'sumHours': floor(sumHours*100)/100.0, 'sumAmount': floor(sumAmount*100)/100.0})
    print(items)

    return render(
        request,
        'evaluation.html',
        context={
            'today': datetime.datetime.now().date(),
            'items': items,
            'sum': floor(tipsSum*100)/100.0,
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
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Tip

from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.all()

from tips.forms import Form
from django.http import HttpResponseRedirect, HttpResponse

from django.http.multipartparser import MultiPartParser

from django.utils import timezone
import json

import datetime

def index(request):
    if request.method == 'POST':
        form = Form(request.POST)

        request_data = request.body

        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, amount in form_data.items():
            user = User.objects.get(id=user_id)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Tip.objects.create(user=user, amount=amount, date=date)

        return HttpResponse(200)
    else:
        form = Form()
        context = {
            'users': users,
            'form': form,
        }
    return render(
        request,
        'tips.html',
        context,
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
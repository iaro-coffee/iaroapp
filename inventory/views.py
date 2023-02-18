from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Product

from django.contrib.auth import get_user_model
from tips.forms import Form
from django.http import HttpResponseRedirect, HttpResponse

def index(request):

    User = get_user_model()
    users = User.objects.all()

    form = Form()
    context = {
        'users': users,
        'form': form,
    }

    return render(
        request,
        'inventory.html',
        context,
    )
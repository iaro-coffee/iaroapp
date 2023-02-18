from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Product

from django.contrib.auth import get_user_model
from tips.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
import json

def index(request):

    User = get_user_model()
    users = User.objects.all()
    products = Product.objects.all()
    form = Form()
    categories = []

    for product in products:
        for category in product.category.all():
            if category not in categories:
                categories.append(category)

    if request.method == 'POST':

        form = Form(request.POST)

        request_data = request.body

        form_data = json.loads(request_data.decode("utf-8"))
        for product, value in form_data.items():
            Product.objects.filter(id=product).update(value=value)
        return HttpResponse(200)

    else:

        context = {
            'users': users,
            'form': form,
            'products': products,
            'categories': categories,
            'isSubmittedToday': False
        }

        return render(
            request,
            'inventory.html',
            context,
        )
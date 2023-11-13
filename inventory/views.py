from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Product
from iaroapp.models import Branch

from django.contrib.auth import get_user_model
from tips.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
import json
import datetime
from django.forms.models import model_to_dict

def index(request, branch='All'):

    User = get_user_model()
    users = User.objects.all()
    products = Product.objects.all()
    branches = Branch.objects.all()
    form = Form()
    categories = []

    if (branch != 'All'):

        # Get storages for selected branch
        branch = branches.filter(name=branch)[0]
        storages = branch.storages.all()
        storages = list(storages)

        # Filter products only available in specific storage of branch
        products = products.filter(storage__name__in=storages)

    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)

    # Add 'All' option to branche selection
    branches = list(branches)
    if (branch != 'All'):
        branches.append('All')

    # Populate available categories
    for product in products:
        for category in product.category.all():
            if category not in categories:
                categories.append(category)

    if request.method == 'POST':

        form = Form(request.POST)

        request_data = request.body

        form_data = json.loads(request_data.decode("utf-8"))
        for product, value in form_data.items():
            if value:
                value = value.replace(',','.')
                if float(value) >= 0:
                    Product.objects.filter(id=product).update(value=value)
        return HttpResponse(200)

    else:

        isSubmittedToday = False
        last_modified_date = "Unknown"
        product_last_modified = Product.objects.latest('modified_date')
        if product_last_modified:
            last_modified_date = product_last_modified.modified_date.date()
            today = datetime.datetime.today().date()
            if last_modified_date == today:
                isSubmittedToday = True

        context = {
            'users': users,
            'form': form,
            'products': products,
            'categories': categories,
            'isSubmittedToday': isSubmittedToday,
            'modifiedDate': last_modified_date,
            'branches': branches,
            'branch': branch,
        }

        return render(
            request,
            'inventory.html',
            context,
        )

from django.contrib.auth.decorators import user_passes_test

def check_admin(user):
   return user.is_superuser

#@user_passes_test(check_admin)
def inventory_evaluation(request):

    products = Product.objects.all()
    products = products.order_by('category')
    #sorted(products,  key=lambda m: -m.value_tobuy)
    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.tobuy:
            sellers.append(prod.display_seller())
    
    product = Product.objects.filter(id=1)
    modified_date = "Unknown"

    if product.exists():
        modified_date = product.first().modified_date.date()

    return render(
        request,
        'inventory_evaluation.html',
        context={
            'products': products,
            'modifiedDate': modified_date,
            'sellers': sellers
        },
    )
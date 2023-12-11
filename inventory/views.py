from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
import json
import datetime
from django.forms.models import model_to_dict
from .models import Product, ProductStorage, Branch, Storage
from django.db.models import Count

def inventory_populate(request):

    User = get_user_model()
    users = User.objects.all()
    products = Product.objects.all()
    branches = Branch.objects.all()
    form = Form()
    storages = []

    branch = request.GET.get('branch')
    if not branch:
        departmentId = request.session.get('departmentId', None)
        if departmentId is not None:
            branch = Branch.objects.filter(departmentId=departmentId).first()
            if branch is not None:
                branch_name = branch.name
            else:
                branch_name = Branch.objects.first().name
        else:
            branch_name = Branch.objects.first().name
        branch = branch_name

    if (branch != 'All'):

        # Get storages for selected branch
        branch = branches.filter(name=branch)[0]
        selected_branch = branch
        storages = branch.storages.all()
        storages = list(storages)

        # Filter products only available in specific storage of branch
        products = products.filter(product_storages__storage__name__in=storages)

    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    # Add 'All' option to branche selection
    branches = list(branches)
    if (branch != 'All'):
        branches.append('All')

    # Populate available storages
    filtered_storages = []
    product_ids = products.values_list('id', flat=True)
    product_storages = ProductStorage.objects.filter(product__id__in=product_ids)
    if branch != 'All':
        for storage in product_storages:
            if storage.storage in storages:
                filtered_storages.append(storage.storage)
    else:
        filtered_storages = [storage.storage for storage in product_storages]
    storages = filtered_storages

    # Sort storages by name
    storages_queryset = Storage.objects.filter(id__in=[storage.id for storage in storages])
    storages_sorted = storages_queryset.order_by('name')
    storages = [storage for storage in storages_sorted]

    if request.method == 'POST':

        form = Form(request.POST)

        request_data = request.body

        form_data = json.loads(request_data.decode("utf-8"))
        for product, value in form_data.items():
            if value['value'] and float(value['value']) >= 0:
                product_instance = Product.objects.get(id=product)
                product_storage_instance = ProductStorage.objects.get(product=product_instance, storage_id=value['storage'])
                product_storage_instance.value = value['value'].replace(',','.')
                product_storage_instance.save()
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
            'storages': storages,
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

def inventory_evaluation(request):

    products = Product.objects.all()
    storages = Storage.objects.all()

    # Sort branches by name, filter out empty ones
    branches = Branch.objects.annotate(num_products=Count('storages__productstorage__product'))
    branches = branches.filter(num_products__gt=0)
    branches = branches.order_by('name')

    # Get last product modification date    
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
            'storages': storages,
            'branches': branches,
        },
    )

def inventory_shopping(request):

    products = Product.objects.all()
    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.oos:
            sellers.append(prod.display_seller())
    
    product = Product.objects.filter(id=1)
    modified_date = "Unknown"

    if product.exists():
        modified_date = product.first().modified_date.date()

    return render(
        request,
        'inventory_shopping.html',
        context={
            'products': products,
            'modifiedDate': modified_date,
            'sellers': sellers
        },
    )

def inventory_packaging(request):

    branches = Branch.objects.all()
    product_storages_set = set()
    for product_storage in ProductStorage.objects.all():
        if product_storage.oos == True and product_storage.main_storage == False:
            product_storages_set.add(product_storage)
    branches_set = set()
    for product_storage in product_storages_set:
        branches_set.add(product_storage.branch)
    branches = list(branches_set)

    products = Product.objects.all()

    # Estimate last DB update    
    product = Product.objects.filter(id=1)
    product_storages = ProductStorage.objects.filter(product__in=products)
    modified_date = "Unknown"
    if product.exists():
        modified_date = product.first().modified_date.date()

    return render(
        request,
        'inventory_packaging.html',
        context={
            'products': products,
            'product_storages': product_storages,
            'modifiedDate': modified_date,
            'branches': branches,
        },
    )
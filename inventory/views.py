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

def getCurrentBranch(request):
    branch = request.GET.get('branch')
    if branch == "All":
        return branch
    if not branch:
        departmentId = request.session.get('departmentId', None)
        if departmentId:
            branch = Branch.objects.filter(departmentId=departmentId).first()
            if branch:
                return branch
    else:
        branch = Branch.objects.filter(name=branch).first()
        if branch:
            return branch
    return Branch.objects.first()

def getAvailableBranchesFiltered(branch):
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    # Sort branches by name, filter out empty ones
    branches = branches.annotate(num_products=Count('storages__productstorage__product'))
    branches = branches.filter(num_products__gt=0)
    branches = branches.order_by('name')
    # Add 'All' option to branche selection
    branches = list(branches)
    if (branch != 'All'):
        branches.append('All')
    return branches

def getInventoryModifiedDate():
   modified_date = Product.objects.order_by('-modified_date').first().modified_date.date() if Product.objects.exists() else None
   return modified_date if modified_date else "Unknown"

def inventory_populate(request):

    User = get_user_model()
    users = User.objects.all()
    products = Product.objects.all()
    branches = Branch.objects.all()
    form = Form()
    storages = []

    # Get current branch by GET parameter or Planday query
    branch = getCurrentBranch(request)

    if (branch != 'All'):

        # Get storages for selected branch
        branch = branches.filter(name=branch)[0]
        selected_branch = branch
        storages = branch.storages.all()
        storages = list(storages)

        # Filter products only available in specific storage of branch
        product_storages = ProductStorage.objects.filter(storage__name__in=storages)
        product_ids = product_storages.values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)

    # Get list of branches which are not selected
    branches = getAvailableBranchesFiltered(branch)

    # Populate available non-empty storages of selected branch
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
            if value['value'] and float(value['value'].replace(',','.')) >= 0:
                product_instance = Product.objects.get(id=product)
                product_storage_instance = ProductStorage.objects.get(product=product_instance, storage_id=value['storage'])
                product_storage_instance.value = value['value'].replace(',','.')
                product_storage_instance.save()
        return HttpResponse(200)

    else:

        # Get last product modification date
        modified_date = getInventoryModifiedDate()

        # Check if inventory already submitted for today
        isSubmittedToday = False
        today = datetime.datetime.today().date()
        if modified_date == today:
            isSubmittedToday = True        

        context = {
            'users': users,
            'form': form,
            'products': products,
            'storages': storages,
            'isSubmittedToday': isSubmittedToday,
            'modifiedDate': modified_date,
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

    # Get current branch by GET parameter or Planday query
    branch = getCurrentBranch(request)

    # Get list of branches which are not selected
    branches = getAvailableBranchesFiltered(branch)

    if (branch != 'All'):

        # Get storages for selected branch
        storages = branch.storages.all()
        storages = list(storages)

        # Filter products only available in specific storage of branch
        product_storages = ProductStorage.objects.filter(storage__name__in=storages)
        product_ids = product_storages.values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)

    # Get last product modification date
    modified_date = getInventoryModifiedDate()

    # Populate available non-empty storages of selected branch
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

    return render(
        request,
        'inventory_evaluation.html',
        context={
            'products': products,
            'modifiedDate': modified_date,
            'storages': storages,
            'branches': branches,
            'branch': branch,
        },
    )

def inventory_shopping(request):

    products = Product.objects.all()
    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.oos:
            sellers.append(prod.display_seller())
    
    # Get last product modification date
    modified_date = getInventoryModifiedDate()

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

    # Get current branch by GET parameter or Planday query
    branch = getCurrentBranch(request)

    # Get source branches
    main_storage_branches = set()
    for product in Product.objects.all():
        for product_storage in product.product_storages.all():
            if product_storage.main_storage and product_storage.oos:
                main_storage_branches.add(product_storage.branch)
    branches = list(main_storage_branches)
    branches = list(set(branches) - {branch})
    if (branch != 'All'):
        branches.append('All')

    # Get target branches
    target_branches = Branch.objects.all()
    product_storages_set = set()
    for product_storage in ProductStorage.objects.all():
        if product_storage.oos == True and product_storage.main_storage == False:
            product_storages_set.add(product_storage)
    branch_counts = {}
    for product_storage in product_storages_set:
        if product_storage.branch not in branch_counts:
            branch_counts[product_storage.branch] = []
        branch_counts[product_storage.branch].append(product_storage)
    target_branches_set = set()
    for product_branch, product_storages in branch_counts.items():
        if len(product_storages) > 1:
            target_branches_set.add(product_branch)
    target_branches = list(target_branches_set)
    target_branches = list(set(target_branches) - {branch})

    # Get storages which require packaging
    filtered_products = set()
    products = Product.objects.all()
    product_storages = ProductStorage.objects.filter(product__in=products)

    # Get last product modification date
    modified_date = getInventoryModifiedDate()

    return render(
        request,
        'inventory_packaging.html',
        context={
            'products': products,
            'product_storages': product_storages,
            'modifiedDate': modified_date,
            'branches': branches,
            'branch': branch,
            'target_branches': target_branches,
        },
    )
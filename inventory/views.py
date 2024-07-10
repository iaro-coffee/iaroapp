import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import redirect, render, reverse

from .forms import ProductFormset
from .models import Branch, Product, ProductStorage, Seller, Storage


def get_current_branch(request):
    # Get branch from the GET parameter
    branch_name = request.GET.get("branch")

    if branch_name == "All":
        return branch_name

    # If a specific branch is selected, return that
    if branch_name:
        branch = Branch.objects.filter(name=branch_name).first()
        if branch:
            return branch

    # If no branch is specified, try to get it from user's profile
    if request.user.is_authenticated:
        profile = request.user.profile
        if profile and profile.branch:
            return profile.branch

    # As a last resort, return the first branch in the system
    return Branch.objects.first()


def getAvailableBranchesFiltered(branch):
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    # Sort branches by name, filter out empty ones
    branches = branches.annotate(
        num_products=Count("storages__productstorage__product")
    )
    branches = branches.filter(num_products__gt=0)
    branches = branches.order_by("name")
    # Add 'All' option to branche selection
    branches = list(branches)
    if branch != "All":
        branches.append("All")
    return branches


def getInventoryModifiedDate():
    modified_date = (
        Product.objects.order_by("-modified_date").first().modified_date.date()
        if Product.objects.exists()
        else None
    )
    return modified_date if modified_date else "Unknown"


def inventory_populate(request):
    current_branch = get_current_branch(request)
    if request.method == "POST":
        ProductFormset(request.POST).save()  # Ensure the formset is saved

        for key, value in request.POST.items():
            if "value" in key and value:
                value = float(value.replace(",", "."))
                product_id = key.split("_")[1]
                storage_id = key.split("_")[2]

                product_instance = Product.objects.get(id=product_id)
                product_storage_instances = ProductStorage.objects.filter(
                    product=product_instance, storage_id=storage_id
                )
                if product_storage_instances.exists():
                    product_storage_instance = product_storage_instances.first()
                    product_storage_instance.value = value
                    product_storage_instance.save()

        messages.success(request, "Inventory submitted successfully.")
        return redirect(
            f"{reverse('inventory_populate')}?branch={current_branch.name if current_branch != 'All' else 'All'}"
        )

    else:
        User = get_user_model()
        users = User.objects.all()
        products = Product.objects.all()
        branches = Branch.objects.all()
        storages = []

        # Get current branch by GET parameter or Planday query
        branch = get_current_branch(request)

        if branch != "All":
            # Get storages for selected branch
            branch = branches.filter(name=branch)[0]
            storages = branch.storages.all()
            storages = list(storages)

            # Filter products only available in specific storage of branch
            product_storages = ProductStorage.objects.filter(storage__name__in=storages)
            product_ids = product_storages.values_list("product_id", flat=True)
            products = Product.objects.filter(id__in=product_ids)

        # Get list of branches which are not selected
        branches = getAvailableBranchesFiltered(branch)

        # Populate available non-empty storages of selected branch
        filtered_storages = []
        product_ids = products.values_list("id", flat=True)
        product_storages = ProductStorage.objects.filter(product__id__in=product_ids)
        if branch != "All":
            for storage in product_storages:
                if storage.storage in storages:
                    filtered_storages.append(storage.storage)
        else:
            filtered_storages = [storage.storage for storage in product_storages]
        storages = filtered_storages

        # Sort storages by name
        storages_queryset = Storage.objects.filter(
            id__in=[storage.id for storage in storages]
        )
        storages_sorted = storages_queryset.order_by("name")
        storages = [storage for storage in storages_sorted]

        # Get last product modification date
        modified_date = getInventoryModifiedDate()

        # Check if inventory already submitted for today
        isSubmittedToday = False
        today = datetime.datetime.today().date()
        if modified_date == today:
            isSubmittedToday = True

        formset = ProductFormset(queryset=products)

        return render(
            request,
            "inventory.html",
            context={
                "pageTitle": "Inventory update",
                "users": users,
                "storages": storages,
                "isSubmittedToday": isSubmittedToday,
                "modifiedDate": modified_date,
                "branches": branches,
                "branch": branch,
                "formset": formset,
                "product_storages": product_storages,  # Ensure product_storages is in context
            },
        )


def check_admin(user):
    return user.is_superuser


def inventory_evaluation(request):
    products = Product.objects.all()
    storages = Storage.objects.all()

    # Get current branch by GET parameter or Planday query
    branch = get_current_branch(request)

    # Get list of branches which are not selected
    branches = getAvailableBranchesFiltered(branch)

    if branch != "All":
        # Get storages for selected branch
        storages = branch.storages.all()
        storages = list(storages)

        # Filter products only available in specific storage of branch
        product_storages = ProductStorage.objects.filter(storage__name__in=storages)
        product_ids = product_storages.values_list("product_id", flat=True)
        products = Product.objects.filter(id__in=product_ids)

    # Get last product modification date
    modified_date = getInventoryModifiedDate()

    # Populate available non-empty storages of selected branch
    filtered_storages = []
    product_ids = products.values_list("id", flat=True)
    product_storages = ProductStorage.objects.filter(product__id__in=product_ids)
    if branch != "All":
        for storage in product_storages:
            if storage.storage in storages:
                filtered_storages.append(storage.storage)
    else:
        filtered_storages = [storage.storage for storage in product_storages]
    storages = filtered_storages

    # Sort storages by name
    storages_queryset = Storage.objects.filter(
        id__in=[storage.id for storage in storages]
    )
    storages_sorted = storages_queryset.order_by("name")
    storages = [storage for storage in storages_sorted]

    print(product_storages)
    return render(
        request,
        "inventory_evaluation.html",
        context={
            "pageTitle": "Inventory overview",
            "products": products,
            "modifiedDate": modified_date,
            "storages": storages,
            "branches": branches,
            "branch": branch,
            "product_storages": product_storages,
        },
    )


def inventory_shopping(request):
    branches = Branch.objects.all()
    branch_id = request.GET.get("branch", "all")
    is_weekly_param = request.GET.get("weekly", "False")

    if is_weekly_param is None or is_weekly_param.lower() == "false":
        is_weekly = False
    else:
        is_weekly = True

    if branch_id == "all":
        selected_branch = None
    else:
        try:
            selected_branch = branches.get(id=branch_id)
        except Branch.DoesNotExist:
            selected_branch = None

    if selected_branch:
        products = Product.objects.filter(
            seller__visibility=Seller.VisibilityChoices.SHOPPING_LIST,
            seller__is_weekly=is_weekly,
            branch=selected_branch,
        )
    else:
        products = Product.objects.filter(
            seller__visibility=Seller.VisibilityChoices.SHOPPING_LIST,
            seller__is_weekly=is_weekly,
        )

    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.has_shortage:
            sellers.append(prod.display_seller())

    modified_date = getInventoryModifiedDate()

    return render(
        request,
        "inventory_shopping.html",
        context={
            "pageTitle": "Shopping list",
            "products": products,
            "modifiedDate": modified_date,
            "sellers": sellers,
            "branches": branches,
            "selected_branch": selected_branch,
            "branch_id": branch_id,
            "is_weekly": is_weekly,
        },
    )


def inventory_production(request):
    products = Product.objects.filter(
        seller__visibility=Seller.VisibilityChoices.PRODUCTION
    )
    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.has_shortage:
            sellers.append(prod.display_seller())

    # TODO(Rapha) get product for every branch where it has a shortage. So we can make production/baking plan per branch

    # Get last product modification date
    modified_date = getInventoryModifiedDate()

    return render(
        request,
        "inventory_production.html",
        context={
            "pageTitle": "Production",
            "products": products,
            "modifiedDate": modified_date,
            "sellers": sellers,
        },
    )


def inventory_packaging(request):
    # Get current branch by GET parameter or Planday query
    branch = get_current_branch(request)

    # Get source branches
    main_storage_branches = set()
    for product in Product.objects.all():
        for product_storage in product.product_storages.all():
            if product_storage.main_storage and product_storage.has_shortage:
                main_storage_branches.add(product_storage.branch)
    branches = list(main_storage_branches)
    branches = list(set(branches) - {branch})
    if branch != "All":
        branches.append("All")

    # Get target branches
    target_branches = Branch.objects.all()
    product_storages_set = set()
    for product_storage in ProductStorage.objects.all():
        if (
            product_storage.has_shortage is True
            and product_storage.main_storage is False
        ):
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
    products = Product.objects.all()
    product_storages = ProductStorage.objects.filter(product__in=products)

    # Get last product modification date
    modified_date = getInventoryModifiedDate()

    return render(
        request,
        "inventory_packaging.html",
        context={
            "pageTitle": "Packaging",
            "products": products,
            "product_storages": product_storages,
            "modifiedDate": modified_date,
            "branches": branches,
            "branch": branch,
            "target_branches": target_branches,
        },
    )

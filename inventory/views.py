import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Prefetch
from django.shortcuts import redirect, render, reverse
from django.utils import timezone

from iaroapp.query_helpers import qif

from .forms import ProductFormset
from .models import Branch, Product, ProductStorage, Seller, Storage

logger = logging.getLogger(__name__)


def get_current_branch(request):
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
        profile = request.user.employeeprofile
        if profile and profile.branch:
            return profile.branch

    # As a last resort, return the first branch in the system
    return Branch.objects.first()


def get_available_branches_filtered(branch):
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    # Sort branches by name, filter out empty ones
    branches = branches.order_by("name")
    # Add 'All' option to branch selection
    branches = list(branches)
    if branch != "All":
        branches.append("All")
    return branches


def get_inventory_modified_date(branch):
    latest_update = (
        ProductStorage.objects.filter(qif(storage__branch=branch, _if=branch != "All"))
        .order_by("-last_updated")
        .first()
    )
    if not latest_update:
        return "Unknown"
    return latest_update.last_updated.date()


def inventory_populate(request):
    # Get the current branch from the request
    current_branch = get_current_branch(request)

    if request.method == "POST":
        # Save the product formset with the posted data
        ProductFormset(request.POST).save()

        # Ensure all database operations within this block are atomic
        with transaction.atomic():
            updates = []
            # Iterate through posted items to find and update product storage values
            for key, value in request.POST.items():
                if "value" in key and value:
                    # Convert the value to float, handling comma as decimal separator
                    value = float(value.replace(",", "."))
                    product_id, storage_id = key.split("_")[1], key.split("_")[2]

                    # Fetch the product storage instance to be updated
                    product_storage_instance = (
                        ProductStorage.objects.select_for_update()
                        .filter(product_id=product_id, storage_id=storage_id)
                        .first()
                    )
                    if product_storage_instance:
                        product_storage_instance.value = value
                        product_storage_instance.last_updated = timezone.now()
                        updates.append(product_storage_instance)

            # Perform a bulk update if there are any updates collected
            if updates:
                ProductStorage.objects.bulk_update(updates, ["value", "last_updated"])

        # Set a success message and redirect to the inventory page with the current branch
        messages.success(request, "Inventory submitted successfully.")
        return redirect(
            f"{reverse('inventory_populate')}?branch={current_branch.name if current_branch != 'All' else 'All'}"
        )

    else:
        # Fetch all users and branches, and add 'All' to the list of branches
        users = get_user_model().objects.all()
        branches = list(Branch.objects.all())
        branches.insert(0, "All")
        modified_date = get_inventory_modified_date(current_branch)

        storages = get_inventory_data_of_branch(current_branch)

        formset = ProductFormset(queryset=Product.objects.none())

        return render(
            request,
            "inventory.html",
            context={
                "pageTitle": "Inventory update",
                "users": users,
                "storages": storages,
                "modifiedDate": modified_date,
                "branches": branches,
                "branch": current_branch,
                "formset": formset,
            },
        )


def check_admin(user):
    return user.is_superuser


def get_inventory_data_of_branch(branch):
    return (
        Storage.objects.filter(qif(branch=branch, _if=branch != "All"))
        .exclude(products=None)
        .prefetch_related(
            Prefetch(
                "productstorage_set",
                ProductStorage.objects.select_related("product"),
            )
        )
    )


def inventory_evaluation(request):
    current_branch = get_current_branch(request)

    # Get list of branches which are not selected
    branches = get_available_branches_filtered(current_branch)

    storages = get_inventory_data_of_branch(current_branch)

    # Get last product modification date
    modified_date = get_inventory_modified_date(current_branch)

    return render(
        request,
        "inventory_evaluation.html",
        context={
            "pageTitle": "Inventory overview",
            "modifiedDate": modified_date,
            "storages": storages,
            "branches": branches,
            "branch": current_branch,
        },
    )


def inventory_shopping(request):
    current_branch = get_current_branch(request)
    branches = get_available_branches_filtered(current_branch)
    is_weekly_param = request.GET.get("weekly", "False")

    if is_weekly_param is None or is_weekly_param.lower() == "false":
        is_weekly = False
    else:
        is_weekly = True

    products = Product.objects.filter(
        qif(branch=current_branch, _if=current_branch != "All"),
        seller__visibility=Seller.VisibilityChoices.SHOPPING_LIST,
        seller__is_weekly=is_weekly,
    )

    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.has_shortage:
            sellers.append(prod.display_seller())

    modified_date = get_inventory_modified_date(current_branch)

    return render(
        request,
        "inventory_shopping.html",
        context={
            "pageTitle": "Shopping list",
            "products": products,
            "modifiedDate": modified_date,
            "sellers": sellers,
            "branches": branches,
            "branch": current_branch,
            "is_weekly": is_weekly,
        },
    )


def inventory_production(request):
    current_branch = get_current_branch(request)
    products = Product.objects.filter(
        seller__visibility=Seller.VisibilityChoices.PRODUCTION
    )
    sellers = []
    for prod in products:
        if (prod.display_seller() not in sellers) and prod.has_shortage:
            sellers.append(prod.display_seller())

    # TODO(Rapha) get product for every branch where it has a shortage. So we can make production/baking plan per branch

    modified_date = get_inventory_modified_date(current_branch)

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
    current_branch = get_current_branch(request)
    branches = get_available_branches_filtered(current_branch)

    branch_deliveries = {}

    if current_branch == "All":
        # Fetch all product storages with shortages across all branches
        product_storages_with_shortage = (
            ProductStorage.objects.filter(main_storage=False, value__lt=F("threshold"))
            .select_related("product", "storage__branch", "storage")
            .prefetch_related("product__unit")
        )

        # Group by target branch
        for ps in product_storages_with_shortage:
            target_branch = ps.storage.branch
            if target_branch not in branch_deliveries:
                branch_deliveries[target_branch] = []
            branch_deliveries[target_branch].append(ps)

    else:
        # Fetch product storages with shortages for the current branch's main storage
        product_storages_with_shortage = (
            ProductStorage.objects.filter(
                product__product_storages__storage__branch=current_branch,
                product__product_storages__main_storage=True,
                main_storage=False,
                value__lt=F("threshold"),
            )
            .select_related("product", "storage__branch", "storage")
            .prefetch_related("product__unit")
        )

        # Group by target branch
        for ps in product_storages_with_shortage:
            target_branch = ps.storage.branch
            if target_branch not in branch_deliveries:
                branch_deliveries[target_branch] = []
            branch_deliveries[target_branch].append(ps)

    # Send the data to the template
    modified_date = get_inventory_modified_date(
        current_branch if current_branch != "All" else None
    )

    return render(
        request,
        "inventory_packaging.html",
        context={
            "pageTitle": "Packaging",
            "branch_deliveries": branch_deliveries,
            "modifiedDate": modified_date,
            "branches": branches,
            "branch": current_branch,
        },
    )

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
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
        profile = request.user.profile
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
        .order_by("last_updated")
        .first()
        .last_updated.date()
    )
    if not latest_update:
        return "Unknown"
    return latest_update


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

    if current_branch == "All":
        products = Product.objects.filter(
            seller__visibility=Seller.VisibilityChoices.SHOPPING_LIST,
            seller__is_weekly=is_weekly,
        )
    else:
        products = Product.objects.filter(
            seller__visibility=Seller.VisibilityChoices.SHOPPING_LIST,
            seller__is_weekly=is_weekly,
            branch=current_branch,
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

    # Determine the target branches
    product_storages_with_shortage = [
        product_storage
        for product_storage in ProductStorage.objects.filter(main_storage=False)
        if product_storage.has_shortage
    ]

    target_branches_set = {
        product_storage.storage.branch
        for product_storage in product_storages_with_shortage
    }

    if current_branch == "All":
        target_branches = list(target_branches_set)
    else:
        target_branches = list(target_branches_set.difference({current_branch}))

    # Get products and related storages
    products = Product.objects.prefetch_related("product_storages", "unit")

    # Dictionary to track deliverable products for each target branch
    branch_deliveries = {}
    for target_branch in target_branches:
        deliverable_products = []
        for product in products:
            if (
                product.needs_packaging()
                and target_branch in product.get_storage_branches
            ):
                oos_value_shipping = product.get_oos_value_shipping()
                for product_storage, data in oos_value_shipping.items():
                    if product_storage == target_branch and data["value_needed"] > 0:
                        deliverable_products.append(product)
                        break
        if deliverable_products:
            branch_deliveries[target_branch] = deliverable_products

    # Filter out empty branches
    branch_deliveries = {k: v for k, v in branch_deliveries.items() if v}

    modified_date = get_inventory_modified_date(current_branch)

    return render(
        request,
        "inventory_packaging.html",
        context={
            "pageTitle": "Packaging",
            "products": products,
            "product_storages": product_storages_with_shortage,
            "modifiedDate": modified_date,
            "branches": branches,
            "branch": current_branch,
            "branch_deliveries": branch_deliveries,
        },
    )

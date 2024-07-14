import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import redirect, render, reverse
from django.utils import timezone

from .forms import ProductFormset
from .models import Branch, Product, ProductStorage, Seller, Storage

logger = logging.getLogger(__name__)


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
        User = get_user_model()
        users = User.objects.all()
        branches = list(Branch.objects.all())
        branches.insert(0, "All")

        # Get the current branch again (could be redundant, consider refactoring)
        branch = get_current_branch(request)
        if branch == "All":
            # Fetch all product storages excluding those with null products
            product_storages = ProductStorage.objects.select_related(
                "storage", "product"
            ).exclude(product__isnull=True)

            # Get distinct storage IDs that have products
            storage_ids_with_products = product_storages.values_list(
                "storage_id", flat=True
            ).distinct()

            # Fetch storages that match the storage IDs
            storages = Storage.objects.filter(
                id__in=storage_ids_with_products
            ).order_by("name")
        else:
            # Fetch the branch object and its storages that have products
            branch_obj = (
                Branch.objects.prefetch_related("storages").filter(name=branch).first()
            )
            if branch_obj:
                storages = branch_obj.storages.annotate(
                    has_products=Exists(
                        ProductStorage.objects.filter(storage=OuterRef("pk")).exclude(
                            product__isnull=True
                        )
                    )
                ).filter(has_products=True)

                # Fetch product storages that match the storages in the branch
                product_storages = (
                    ProductStorage.objects.filter(storage__in=storages)
                    .select_related("storage", "product")
                    .exclude(product__isnull=True)
                )

        # Get the last modified date for the inventory
        modified_date = getInventoryModifiedDate()

        # Create an empty product formset
        formset = ProductFormset(queryset=Product.objects.none())

        # Render the inventory template with the context data
        return render(
            request,
            "inventory.html",
            context={
                "pageTitle": "Inventory update",
                "users": users,
                "storages": storages,
                "modifiedDate": modified_date,
                "branches": branches,
                "branch": branch,
                "formset": formset,
                "product_storages": product_storages,
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
    branch = get_current_branch(request)

    # Get branches with main storage having shortages
    main_storage_branches = {
        ps.storage.branches.first()
        for product in Product.objects.all()
        for ps in product.product_storages.all()
        if ps.main_storage and ps.has_shortage
    }
    branches = list(main_storage_branches.difference({branch}))
    if branch != "All":
        branches.append("All")

    # Determine the target branches
    product_storages_with_shortage = [
        ps
        for ps in ProductStorage.objects.filter(main_storage=False)
        if ps.has_shortage
    ]
    target_branches_set = {
        ps.storage.branches.first() for ps in product_storages_with_shortage
    }

    # Handle the case when a specific branch is selected
    if branch != "All":
        target_branches = [branch]
    else:
        target_branches = list(target_branches_set.difference({branch}))

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

    modified_date = getInventoryModifiedDate()

    return render(
        request,
        "inventory_packaging.html",
        context={
            "pageTitle": "Packaging",
            "products": products,
            "product_storages": product_storages_with_shortage,
            "modifiedDate": modified_date,
            "branches": branches,
            "branch": branch,
            "branch_deliveries": branch_deliveries,
        },
    )

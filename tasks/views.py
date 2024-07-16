import logging
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.generic import ListView

from inventory.models import Branch
from users.models import Profile

from .forms import BakingPlanForm, TaskForm, TaskFormset
from .models import (
    BakingPlanInstance,
    Recipe,
    Task,
    TaskBranchDayOrder,
    TaskInstance,
    Weekdays,
)

logger = logging.getLogger(__name__)


class TasksView(LoginRequiredMixin, ListView):
    """Handles task display and updates based on the current branch and day."""

    template_name = "tasks.html"
    formset_class = TaskFormset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        today = timezone.now().date()
        current_day = today.strftime("%A")

        # Check if this is the initial load or if specific parameters are present
        if "day" in self.request.GET or "branch" in self.request.GET:
            selected_day = self.request.GET.get("day", current_day)
            branch_name = self.request.GET.get("branch", "All")
        else:
            # Use the user's profile branch if no specific parameters are present
            user_profile = Profile.objects.get(user=self.request.user)
            branch_name = user_profile.branch.name if user_profile.branch else "All"
            selected_day = current_day

        # Update the context with necessary information
        context.update(
            {
                "selected_day": selected_day,
                "current_day": current_day,
                "today": today,
                "branches": self.get_branches(branch_name),
                "branch": branch_name,
                "is_admin": check_admin(self.request.user),
                "days_of_week": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ],
            }
        )

        # Fetch and order tasks based on the selected day and branch
        tasks = get_my_tasks(self.request, branch_name)
        ordered_tasks = self.get_ordered_tasks(tasks, branch_name, selected_day)

        # Create a formset for the tasks if a specific branch is selected
        formset = (
            self.formset_class(queryset=ordered_tasks) if branch_name != "All" else None
        )
        if formset:
            for form in formset:
                if form.instance.pk and branch_name != "All":
                    form.instance.done_for_branch = form.instance.is_done(
                        get_object_or_404(Branch, name=branch_name)
                    )

        # Update the context with task information and formset
        context.update(
            {
                "pageTitle": "Tasks",
                "task_list": ordered_tasks,
                "formset": formset,
            }
        )

        return context

    def get_branches(self, current_branch_name):
        # Fetch all branches and add an "All" option
        branches = list(Branch.objects.all().order_by("name"))
        branches.append("All")
        return branches

    # Determine which branches to fetch tasks for and handle the special case when all branches are selected
    def get_ordered_tasks(self, tasks, branch_name, selected_day):
        if branch_name != "All":
            branch_obj = get_object_or_404(Branch, name=branch_name)
            return self.order_tasks(tasks, branch_obj.id, selected_day)
        else:
            ordered_tasks = {}
            for br in Branch.objects.all():
                branch_tasks = tasks.filter(branch=br, weekdays__name=selected_day)
                if branch_tasks.exists():
                    ordered_tasks[br.name] = self.order_tasks(
                        branch_tasks, br.id, selected_day
                    )
                else:
                    ordered_tasks[br.name] = []
            return ordered_tasks

    # Focus on the task ordering logic for a specific branch and day
    def order_tasks(self, tasks, branch_id, selected_day):
        # Fetch task orders for the branch and day
        task_orders = (
            TaskBranchDayOrder.objects.filter(
                branch_id=branch_id, weekday__name=selected_day
            )
            .order_by("order")
            .values_list("task_id", flat=True)
        )
        ordered_tasks_ids = list(task_orders)
        unordered_tasks_ids = [
            task.id for task in tasks if task.id not in ordered_tasks_ids
        ]
        ordered_tasks_ids.extend(unordered_tasks_ids)
        return Task.objects.filter(
            id__in=ordered_tasks_ids, weekdays__name=selected_day
        ).order_by(
            models.Case(
                *[
                    models.When(id=task_id, then=pos)
                    for pos, task_id in enumerate(ordered_tasks_ids)
                ]
            )
        )

    def get(self, request, *args, **kwargs):
        # Handle GET request and render the context with the template
        context = self.get_context_data(object_list=request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Handle POST request for updating task order or submitting tasks
        if "order" in request.POST:
            self.update_task_order(request)
        else:
            self.submit_tasks(request)
        return self.redirect_with_query_params(request)

    def update_task_order(self, request):
        # Update the order of tasks based on the provided order
        order = request.POST.get("order", "")
        branch_name = self.request.GET.get("branch", "All")
        selected_day = self.request.GET.get("day", timezone.now().strftime("%A"))
        weekday = Weekdays.objects.get(name=selected_day)

        if branch_name != "All":
            branch_obj = get_object_or_404(Branch, name=branch_name)
            branch_id = branch_obj.id
        else:
            branch_id = None

        if order:
            task_ids = order.split(",")
            for idx, task_id in enumerate(task_ids):
                task = Task.objects.get(pk=task_id)
                task_order, created = TaskBranchDayOrder.objects.get_or_create(
                    task=task, branch_id=branch_id, weekday=weekday
                )
                task_order.order = idx
                task_order.save()
        messages.success(request, "Task order updated successfully.")

    def submit_tasks(self, request):
        # Submit task completion updates
        task_formset = self.formset_class(request.POST)
        user = request.user
        date_done = timezone.now()
        branch_name = self.request.GET.get("branch", "All")

        if branch_name != "All":
            branch = get_object_or_404(Branch, name=branch_name)
        else:
            branch = None

        if task_formset.is_valid():
            for form in task_formset:
                if form.instance.pk:
                    done_field = f"done_{form.instance.id}"
                    if done_field in request.POST and request.POST[done_field] == "on":
                        TaskInstance.objects.create(
                            user=user,
                            date_done=date_done,
                            task=form.instance,
                            branch=branch,
                        )
            messages.success(request, "Tasks submitted successfully.")
        else:
            messages.error(
                request,
                "There was an error with your submission. Please check the form and try again.",
            )
            for form in task_formset:
                print(f"Errors in form {form.instance.pk}: {form.errors}")

    def redirect_with_query_params(self, request):
        # Redirect with the current query parameters (branch and day)
        query_params = QueryDict(mutable=True)
        branch_param = request.GET.get("branch", "All")
        query_params["branch"] = branch_param
        query_params["day"] = request.GET.get("day", timezone.now().strftime("%A"))
        url = reverse("tasks") + "?" + query_params.urlencode()
        return redirect(url)


# Function to fetch tasks for the current user based on the day of the week and branch
def get_my_tasks(request, branch_name=None):
    """
    Fetches tasks for the current user based on the day of the week, user's groups, and selected branch.
    Excludes subtasks and optimizes queries to improve performance.
    """
    selected_day = request.GET.get("day", timezone.now().strftime("%A"))
    tasks = Task.objects.filter(
        Q(weekdays__name=selected_day) | Q(weekdays__isnull=True), parent_task=None
    ).prefetch_related("users", "groups", "branch")

    user_groups_ids = request.user.groups.values_list("id", flat=True)

    if branch_name == "All" or branch_name is None:
        branch_filter = Q()
    else:
        branch_filter = Q(branch__name=branch_name)

    filtered_tasks = tasks.filter(
        Q(users=request.user)
        | Q(groups__id__in=user_groups_ids)
        | (Q(users__isnull=True) & Q(groups__isnull=True)),
        branch_filter,
    ).distinct()

    return filtered_tasks


def check_admin(user):
    return user.is_superuser


def check_staff(user):
    return user.is_superuser or user.is_staff


@user_passes_test(check_admin)
def tasks_evaluation(request):
    tasks = Task.objects.all()
    tasks_evaluation = {}
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    weekday_today = datetime.today().strftime("%A")

    for weekday in weekdays:
        tasks_evaluation[weekday] = []
        for task in tasks:
            task = model_to_dict(task)
            task["assignees"] = task["users"] + task["groups"]
            if not task["weekdays"]:
                tasks_evaluation[weekday].append(task)
            for task_weekday in task["weekdays"]:
                if weekday == str(task_weekday):
                    tasks_evaluation[weekday].append(task)

    beginning_of_week = datetime.combine(
        datetime.today() - timedelta(days=datetime.today().weekday() % 7), time()
    )
    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:
        for weekday in weekdays:
            for task in tasks_evaluation[weekday]:
                if "done" not in task:
                    task["done"] = {}
                if task["id"] == task_instance.task.id:
                    if task_instance.date_done is not None:
                        if beginning_of_week.astimezone() < task_instance.date_done:
                            done = {
                                "done_weekday": weekdays[
                                    task_instance.date_done.weekday()
                                ],
                                "done_datetime": task_instance.date_done.strftime(
                                    "%d.%m, %H:%M"
                                ),
                                "done_persons": task_instance.user,
                            }
                            task["done"][
                                weekdays[task_instance.date_done.weekday()]
                            ] = done

    return render(
        request,
        "tasks_list_evaluation.html",
        context={
            "pageTitle": "Tasks overview",
            "tasks": tasks_evaluation,
            "weekdays": weekdays,
            "today": weekday_today,
        },
    )


@user_passes_test(check_admin)
def tasks_baking(request):
    weekday = request.GET.get("weekday")
    weekdays = Weekdays.objects.all()
    if weekday:
        weekday = weekdays.get(name=weekday)
    else:
        weekday = weekdays.first()
    if request.method == "POST":
        form = BakingPlanForm(request.POST)
        if form.is_valid():
            for key, value in request.POST.items():
                if "weekday" in key:
                    weekday = value
                    weekday = Weekdays.objects.get(name=weekday)
                value = value.replace(",", ".")
                if (
                    ("value_ost" in key or "value_west" in key)
                    and value
                    and float(value) > 0
                ):
                    value = float(value)
                    recipe_id = key.split("-")[0]
                    recipe = Recipe.objects.get(id=recipe_id)
                    if "value_ost" in key:
                        branch = "Iaro Ost"
                    else:
                        branch = "Iaro West"
                    branch = Branch.objects.get(name=branch)
                    for weekday_test in weekdays:
                        if weekday_test == weekday:
                            try:
                                instance = BakingPlanInstance.objects.get(
                                    recipe=recipe, branch=branch, weekday=weekday
                                )
                            except BakingPlanInstance.DoesNotExist:
                                instance = BakingPlanInstance.objects.create(
                                    recipe=recipe, branch=branch, value=float(value)
                                )
                            instance.value = float(value)
                            instance.weekday.set([weekday])
                            instance.save()

            messages.success(request, "Baking plan successfully updated!")
            return redirect(reverse("tasks_baking") + "?weekday=" + str(weekday))
        else:
            messages.error(request, "Updating baking plan failed!")
            return redirect(reverse("tasks_baking") + "?weekday=" + str(weekday))
    else:
        recipes = Recipe.objects.all()
        formset = []
        for recipe in recipes:
            form = BakingPlanForm(prefix=str(recipe.id), instance=recipe)
            try:
                baking_plan_instance = BakingPlanInstance.objects.filter(
                    recipe=recipe, weekday=weekday
                )
                value_ost = (
                    baking_plan_instance.filter(branch__name="Iaro Ost")
                    .values_list("value", flat=True)
                    .first()
                )
                value_west = (
                    baking_plan_instance.filter(branch__name="Iaro West")
                    .values_list("value", flat=True)
                    .first()
                )
                if value_ost:
                    form.fields["value_ost"].widget.attrs["placeholder"] = value_ost
                if value_west:
                    form.fields["value_west"].widget.attrs["placeholder"] = value_west
            except ObjectDoesNotExist:
                pass
            formset.append(form)

        bakingplans = BakingPlanInstance.objects.all()
        if bakingplans.exists():
            modified_date = (
                bakingplans.order_by("-modified_date").first().modified_date.date()
            )
            modified_date = modified_date if modified_date else "Unknown"
        else:
            modified_date = "Unknown"

    return render(
        request,
        "tasks_baking.html",
        context={
            "pageTitle": "Baking plan",
            "formset": formset,
            "modifiedDate": modified_date,
            "weekdays": weekdays,
            "weekday": weekday,
        },
    )


@user_passes_test(check_staff)
def tasks_add(request):
    parentTask = request.GET.get("parentTask")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task was added successfully.")
            return redirect("tasks_add")
    else:
        initial_values = {}
        if parentTask:
            initial_values = {"parent_task": int(parentTask)}
        form = TaskForm(initial=initial_values)

    context = {"form": form, "subpage_of": "/tasks"}

    if parentTask:
        context["parentTask"] = parentTask

    return render(
        request,
        "tasks_add.html",
        context,
    )


# Render single task


def task_single(request, taskId):
    branch = request.GET.get("branch")

    if request.method == "POST":

        search_params = request.GET.copy()
        search_params = search_params.get("branch", [])

        user_id = request.user.id
        User = get_user_model()
        user = User.objects.get(id=user_id)
        date = datetime.now()

        for key, value in request.POST.items():
            if "done" in key:
                task_id_done = key.split("_")[1]
                task = Task.objects.get(id=task_id_done)
                TaskInstance.objects.create(user=user, date_done=date, task=task)

        task_single_url = reverse("task_single", args=[taskId])
        if search_params:
            task_single_url += "?branch=" + search_params

        messages.success(request, "Tasks submitted successfully.")
        return redirect(task_single_url)

    task = Task.objects.get(id=taskId)

    context = {
        "task": task,
    }

    if branch:
        context["branch"] = branch

    return render(request, "task_single.html", context)

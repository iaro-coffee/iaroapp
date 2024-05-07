from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render, reverse

from inventory.models import Branch
from inventory.views import getCurrentBranch

from .forms import BakingPlanForm, TaskForm, TaskFormset
from .models import BakingPlanInstance, Recipe, Task, TaskInstance, Weekdays


def getMyTasks(request):
    weekdayToday = datetime.today().strftime("%A")
    weekdayToday = Weekdays.objects.get(name=weekdayToday)

    # Exclude subtasks
    tasks = Task.objects.filter(parent_task=None)

    # TODO(Rapha): filter tasks by not done

    myTasks = []
    for task in tasks:
        userMatch = request.user in task.users.all()
        groupMatch = any(
            group in request.user.groups.all() for group in task.groups.all()
        )
        noUserOrGroup = not task.groups.all() and not task.users.all()
        weekdayMatch = weekdayToday in list(task.weekdays.all())
        if (userMatch or groupMatch or noUserOrGroup) and (
            weekdayMatch or not task.weekdays.exists()
        ):
            myTasks.append(task)

    # Convert the list of tasks to a QuerySet and order by type
    myTasksQuerySet = Task.objects.filter(
        id__in=[task.id for task in myTasks]
    ).order_by("title")

    return myTasksQuerySet


def check_admin(user):
    return user.is_superuser


def check_staff(user):
    return user.is_superuser or user.is_staff


def tasks(request):
    User = get_user_model()

    if request.method == "POST":
        TaskFormset(request.POST)
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        date = datetime.now()

        for key, value in request.POST.items():
            if "done" in key:
                task_id_done = key.split("_")[1]
                task = Task.objects.get(id=task_id_done)
                TaskInstance.objects.create(user=user, date_done=date, task=task)

        messages.success(request, "Tasks submitted successfully.")
        return redirect(reverse("tasks"))

    tasks = getMyTasks(request)
    today = datetime.today().date()

    # Get current branch by GET parameter or Planday query
    branch = getCurrentBranch(request)
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    branches = branches.order_by("name")
    branches = list(branches)
    if branch != "All":
        branches.append("All")
        tasks = tasks.filter(branch=branch)

    formset = TaskFormset(queryset=tasks)

    return render(
        request,
        "tasks.html",
        context={
            "pageTitle": "Tasks",
            "task_list": tasks,
            "today": today,
            "formset": formset,
            "branches": branches,
            "branch": branch,
        },
    )


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
    weekdayToday = datetime.today().strftime("%A")

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
                            done = {}
                            done["done_weekday"] = weekdays[
                                task_instance.date_done.weekday()
                            ]
                            done["done_datetime"] = task_instance.date_done.strftime(
                                "%d.%m, %H:%M"
                            )
                            done["done_persons"] = task_instance.user
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
            "today": weekdayToday,
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

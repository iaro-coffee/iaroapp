from django.shortcuts import render
from .models import Task, TaskInstance
from django.forms.models import model_to_dict
from datetime import datetime, timedelta, time
from operator import itemgetter
from inventory.models import Product
from django.contrib.auth import get_user_model
import json
from django.http import HttpResponse

def getMyTasks(request):
    weekdayToday = datetime.today().strftime('%A')
    tasks = Task.objects.all()
    myTasks = []
    for task in tasks:
        task = model_to_dict(task)
        task['assignees'] = task['users'] + task['groups']
        userMatch = request.user in task['users']
        groupMatch = any(group in request.user.groups.all() for group in task['groups'])
        noUserOrGroup = not task['groups'] and not task['users']
        weekdayMatch = weekdayToday in [str(weekday) for weekday in task['weekdays']] or not task['weekdays']
        if (userMatch or groupMatch or noUserOrGroup) and weekdayMatch:
            task['done'] = False
            myTasks.append(task)

    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:
        for task in myTasks:
            if task['id'] == task_instance.task.id:
                if task_instance.date_done != None:
                    if [task_instance.date_done.strftime('%A') == weekday for weekday in task['weekdays']]:
                        task['date_done'] = task_instance.date_done

    return sorted(myTasks, key=itemgetter('type'))

def check_admin(user):
   return user.is_superuser

def check_staff(user):
   return user.is_superuser or user.is_staff

def tasks(request):

    User = get_user_model()

    if request.method == 'POST':

        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        taskids_completed = list(form_data.keys())
        date = datetime.now()

        for task_id in taskids_completed:
            task = Task.objects.get(id=task_id)
            TaskInstance.objects.create(user=user, date_done=date, task=task)

        return HttpResponse(200)

    tasks = getMyTasks(request)
    today = datetime.today().date()

    return render(
        request,
        'tasks.html',
        context={
            'task_list': tasks,
            'today': today
        },
    )

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(check_admin)
def tasks_evaluation(request):

    tasks = Task.objects.all()
    tasks_evaluation = {}
    weekdays = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]
    weekdayToday = datetime.today().strftime('%A')

    for weekday in weekdays:
        tasks_evaluation[weekday] = []
        for task in tasks:
            task = model_to_dict(task)
            task['assignees'] = task['users'] + task['groups']
            if not task['weekdays']:
                tasks_evaluation[weekday].append(task)
            for task_weekday in task['weekdays']:
                if weekday == str(task_weekday):
                    tasks_evaluation[weekday].append(task)

    beginning_of_week = datetime.combine(datetime.today() - timedelta(days=datetime.today().weekday() % 7), time())
    task_instances = TaskInstance.objects.all()
    for task_instance in task_instances:
        for weekday in weekdays:
            for task in tasks_evaluation[weekday]:
                if 'done' not in task:
                    task['done'] = {}
                if task['id'] == task_instance.task.id:
                    if task_instance.date_done != None:
                        if beginning_of_week.astimezone() < task_instance.date_done:
                            done = {}
                            done['done_weekday'] = weekdays[task_instance.date_done.weekday()]
                            done['done_datetime'] = task_instance.date_done.strftime("%d.%m, %H:%M")
                            done['done_persons'] = task_instance.user
                            task['done'][weekdays[task_instance.date_done.weekday()]] = done

    return render(
        request,
        'tasks_list_evaluation.html',
        context={
            'tasks': tasks_evaluation,
            'weekdays': weekdays,
            'today': weekdayToday
        },
    )

from .forms import BakingPlanForm
from django.forms import modelformset_factory
from django.contrib import messages
from django.shortcuts import redirect, reverse
from inventory.models import Branch, Product, Weekdays
from .models import BakingPlanInstance, Recipe
from django.core.exceptions import ObjectDoesNotExist

@user_passes_test(check_admin)
def tasks_baking(request):

    weekday = request.GET.get('weekday')
    weekdays = Weekdays.objects.all()
    if weekday:
        weekday = weekdays.get(name=weekday)
    else:
        weekday = weekdays.first()
    if request.method == 'POST':
        form = BakingPlanForm(request.POST)
        if form.is_valid():
            for key, value in request.POST.items():
                if "weekday" in key:
                    weekday = value
                    weekday = Weekdays.objects.get(name=weekday)
                value = value.replace(',','.')
                if ("value_ost" in key or "value_west" in key) and value and float(value) > 0:
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
                                instance = BakingPlanInstance.objects.get(recipe=recipe, branch=branch, weekday=weekday)
                            except BakingPlanInstance.DoesNotExist:
                                instance = BakingPlanInstance.objects.create(recipe=recipe, branch=branch, value=float(value))
                            instance.value = float(value)
                            instance.weekday.set([weekday])
                            instance.save()

            messages.success(request, 'Baking plan successfully updated!')
            return redirect(reverse('tasks_baking') + '?weekday='+str(weekday))
        else:
            messages.success(request, 'Updating baking plan failed!')
            return redirect(reverse('tasks_baking') + '?weekday='+str(weekday))
    else:
        recipes = Recipe.objects.all()
        formset = []
        for recipe in recipes:
            form = BakingPlanForm(prefix=str(recipe.id), instance=recipe)
            try:
                baking_plan_instance = BakingPlanInstance.objects.filter(recipe=recipe,weekday=weekday)
                value_ost = baking_plan_instance.filter(branch__name="Iaro Ost").values_list('value', flat=True).first()
                value_west = baking_plan_instance.filter(branch__name="Iaro West").values_list('value', flat=True).first()
                if value_ost:
                    form.fields['value_ost'].widget.attrs['placeholder'] = value_ost
                if value_west:
                    form.fields['value_west'].widget.attrs['placeholder'] = value_west
            except ObjectDoesNotExist:
                placeholder_value = ''
            formset.append(form)

        bakingplans = BakingPlanInstance.objects.all()
        if bakingplans.exists():
            modified_date = bakingplans.order_by('-modified_date').first().modified_date.date()
            modified_date = modified_date if modified_date else "Unknown"
        else:
            modified_date = "Unknown"

    return render(
        request,
        'tasks_baking.html',
        context={
            'formset': formset,
            'modifiedDate': modified_date,
            'weekdays': weekdays,
            'weekday': weekday,
        })


from .forms import TaskForm

@user_passes_test(check_staff)
def tasks_add(request):

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was added successfully.')
            return redirect('tasks_add')
    else:
        form = TaskForm()

    return render(
        request,
        'tasks_add.html',
        context={'form': form},
    )
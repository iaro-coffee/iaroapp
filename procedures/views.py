import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render

from inventory.models import Branch
from inventory.views import get_current_branch

from .models import Procedure
from .procedure_category import ProcedureCategory


@login_required
def index(request):
    if request.method == "POST":
        request_data = request.body
        print(request_data)
        form_data = json.loads(request_data.decode("utf-8"))
        taskids_completed = list(form_data.keys())
        tasks = list(form_data.values())
        date = datetime.now()

        print(tasks)
        for i in range(len(tasks)):
            task = Procedure.objects.get(id=taskids_completed[i])
            print(task)
            if tasks[i]:
                task.date_done = date
            else:
                task.date_done = None
            task.save()

        return HttpResponse(200)


def opening(request):
    procedureModels = Procedure.objects.filter(type=1, groups__user=request.user)
    categoriesModels = ProcedureCategory.objects.filter(
        procedure__type=1, procedure__groups__user=request.user
    ).distinct()
    categories = []
    for category in categoriesModels:
        categories.append(model_to_dict(category))
    procedures = []
    for procedure in procedureModels:
        procedures.append(model_to_dict(procedure))

    # Get current branch by GET parameter or Planday query
    branch = get_current_branch(request).name
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    branches = branches.order_by("name")

    return render(
        request,
        "procedures.html",
        context={
            "pageTitle": "Store opening",
            "procedures": procedures,
            "today": datetime.today().date(),
            "categories": categories,
            "opening": True,
            "branches": branches,
            "branch": branch,
        },
    )


def closing(request):
    procedureModels = Procedure.objects.filter(
        type=2, groups__user=request.user
    ).distinct()
    categoriesModels = ProcedureCategory.objects.filter(
        procedure__type=2, procedure__groups__user=request.user
    ).distinct()
    categories = []
    for category in categoriesModels:
        categories.append(model_to_dict(category))
    procedures = []
    for procedure in procedureModels:
        procedures.append(model_to_dict(procedure))

    # Get current branch by GET parameter or Planday query
    branch = get_current_branch(request).name
    branches = Branch.objects.all()
    # Filter selected branch from available branches
    branches = branches.exclude(name=branch)
    branches = branches.order_by("name")

    return render(
        request,
        "procedures.html",
        context={
            "pageTitle": "Store closing",
            "procedures": procedures,
            "today": datetime.today().date(),
            "categories": categories,
            "closing": True,
            "branches": branches,
            "branch": branch,
        },
    )

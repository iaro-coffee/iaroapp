from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render

from .models import Procedure
import json
from datetime import datetime

from .procedure_category import ProcedureCategory
from inventory.models import Branch

@login_required
def index(request):
    if request.method == 'POST':
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        taskids_completed = list(form_data.keys())
        tasks = list(form_data.values())
        date = datetime.now()

        for i in range(len(tasks)):
            task = Procedure.objects.get(id=taskids_completed[i])
            if (tasks[i]):
                task.date_done = date;
            else:
                task.date_done = None;
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

    branches = Branch.objects.all()
    branches = branches.order_by('name')

    branch = request.GET.get('branch')
    if not branch:
        branch = Branch.objects.first().name

    return render(
        request,
        'procedures.html',
        context={
            'procedures': procedures,
            'today': datetime.today().date(),
            'categories': categories,
            'opening': True,
            'branches': branches,
            'branch': branch,
        },
    )

def closing(request):
    procedureModels = Procedure.objects.filter(type=2, groups__user=request.user).distinct()
    categoriesModels = ProcedureCategory.objects.filter(
        procedure__type=2, procedure__groups__user=request.user
    ).distinct()
    categories = []
    for category in categoriesModels:
        categories.append(model_to_dict(category))
    procedures = []
    for procedure in procedureModels:
        procedures.append(model_to_dict(procedure))

    branches = Branch.objects.all()
    branches = branches.order_by('name')

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

    return render(
        request,
        'procedures.html',
        context={
            'procedures': procedures,
            'today': datetime.today().date(),
            'categories': categories,
            'closing': True,
            'branches': branches,
            'branch': branch,
        },
    )


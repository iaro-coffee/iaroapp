from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import NewUserForm
from .no_planday_email_exception import NoPlandayEmailException


def index(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            try:
                user, employeeGroups = form.save(request)
            except NoPlandayEmailException:
                messages.error(
                    request,
                    "Provided E-Mail does not match any existing planday E-Mail",
                )
            except:
                messages.error(
                    request, "Unsuccessful registration. Invalid information."
                )
            else:
                for group in employeeGroups:
                    if group == 272480:  # Barista
                        user.groups.add(Group.objects.get(name="Barista"))
                    elif group == 274170:  # Kitchen
                        user.groups.add(Group.objects.get(name="Kitchen"))
                    elif group == 275780:  # Service
                        user.groups.add(Group.objects.get(name="Service"))
                user.save()
                login(request, user)
                messages.success(request, "Registration successful.")
                return redirect("/")
    form = NewUserForm()
    return render(
        request=request, template_name="register.html", context={"register_form": form}
    )

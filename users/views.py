from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from users.forms import UserUpdateForm, ProfileUpdateForm

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import NewUserForm
from .no_planday_email_exception import NoPlandayEmailException


class Profile(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form
        }

        return render(
            request=request,
            template_name="profile.html",
            context=context
        )

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(request, "Your profile has been updated successfully")

            return redirect("profile")
        else:
            print(user_form.errors)
            print(profile_form.errors)
            context = {
                "user_form": user_form,
                "profile_form": profile_form
            }
            messages.error(request, "Error updating your profile")

            return render(
                request=request,
                template_name="profile.html",
                context=context
            )


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

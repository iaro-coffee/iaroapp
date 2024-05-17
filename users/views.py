from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from users.forms import UserUpdateForm, ProfileUpdateForm

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import UserClientCreationForm
from .no_planday_email_exception import NoPlandayEmailException

import logging
logger = logging.getLogger(__name__)

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


class RegisterView(FormView):
    template_name = 'register.html'
    form_class = UserClientCreationForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        try:
            user, employeeGroups = form.save(self.request)
            self.assign_user_groups(user, employeeGroups)
            login(self.request, user)
            messages.success(self.request, "Registration successful.")
            return super().form_valid(form)
        except NoPlandayEmailException:
            form.add_error(None, "Provided E-Mail does not match any existing planday E-Mail.")
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            form.add_error(None, "Unsuccessful registration. Invalid information.")
        return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Form is not valid. Please correct the errors below.")
        return super().form_invalid(form)

    def assign_user_groups(self, user, employeeGroups):
        group_mapping = {
            272480: "Barista",
            274170: "Kitchen",
            275780: "Service"
        }
        for group_id in employeeGroups:
            group_name = group_mapping.get(group_id)
            if group_name:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    logger.error(f"Group {group_name} does not exist.")
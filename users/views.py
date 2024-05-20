
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import UserClientCreationForm
from .no_planday_email_exception import NoPlandayEmailException
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserUpdateForm, ProfileUpdateForm

import logging
logger = logging.getLogger(__name__)


class Profile(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        password_form = PasswordChangeForm(user=request.user)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'password_form': password_form
        }

        return render(
            request=request,
            template_name="profile.html",
            context=context
        )

    def post(self, request):
        if 'password_form' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keep user logged in
                messages.success(request, "Your password has been changed successfully")
                return redirect("profile")
            else:
                messages.error(request, "Please correct the error below.")
                user_form = UserUpdateForm(instance=request.user)
                profile_form = ProfileUpdateForm(instance=request.user.profile)
        else:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            password_form = PasswordChangeForm(user=request.user)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Your profile has been updated successfully")
                return redirect("profile")
            else:
                messages.error(request, "Please correct the error below.")

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'password_form': password_form
        }

        return render(
            request=request,
            template_name="profile.html",
            context=context
        )


def clear_messages(request):
    storage = messages.get_messages(request)
    storage.used = True


class LoginView(AuthLoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        clear_messages(self.request)
        messages.success(self.request, "Login successful.")
        logger.info(f"User {form.get_user().username} logged in successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        clear_messages(self.request)
        messages.error(self.request, "Login failed. Please check your username and password.")
        logger.warning(f"Login attempt failed for user {form.data.get('username')}.")
        return super().form_invalid(form)


class RegisterView(FormView):
    template_name = 'register.html'
    form_class = UserClientCreationForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        try:
            user, employeeGroups = form.save()
            self.assign_user_groups(user, employeeGroups)
            login(self.request, user)
            clear_messages(self.request)  # Clear all existing messages
            messages.success(self.request, "Registration successful.")
            return super().form_valid(form)
        except NoPlandayEmailException:
            form.add_error('email', "Provided E-Mail does not match any existing Planday E-Mail.")
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            form.add_error(None, "Unsuccessful registration. Invalid information.")
        return self.form_invalid(form)

    def form_invalid(self, form):
        clear_messages(self.request)
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
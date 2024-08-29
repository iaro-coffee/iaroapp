import logging

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView

from customers.forms import CustomerProfileUpdateForm
from customers.models import CustomerProfile
from interactions.models import Note, NoteReadStatus
from onboarding.models import Document

from .forms import ProfileUpdateForm, UserClientCreationForm, UserUpdateForm
from .models import EmployeeProfile
from .no_planday_email_exception import NoPlandayEmailException

logger = logging.getLogger(__name__)


class EmployeeProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        try:
            profile_form = ProfileUpdateForm(instance=request.user.employeeprofile)
        except ObjectDoesNotExist:
            profile_form = None

        try:
            customer_profile_form = CustomerProfileUpdateForm(
                instance=request.user.customerprofile
            )
            customer_profile = request.user.customerprofile
        except ObjectDoesNotExist:
            customer_profile_form = None
            customer_profile = None

        context = {
            "pageTitle": "Profile",
            "user_form": user_form,
            "profile_form": profile_form,
            "password_form": password_form,
            "customer_profile_form": customer_profile_form,
            "customer_profile": customer_profile,
        }

        return render(request=request, template_name="profile.html", context=context)

    def post(self, request):
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        profile_form = None
        customer_profile_form = None

        if "username" in request.POST or "email" in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            try:
                profile_instance = request.user.employeeprofile
                profile_form = ProfileUpdateForm(
                    request.POST, request.FILES, instance=profile_instance
                )
            except ObjectDoesNotExist:
                profile_form = ProfileUpdateForm(request.POST, request.FILES)

            if user_form.is_valid() and (
                profile_form is None or profile_form.is_valid()
            ):
                user_form.save()
                if profile_form:
                    profile_form.save()
                messages.success(request, "Your profile has been updated successfully")
                return redirect("profile")
            else:
                messages.error(request, "Please correct the error below.")

        elif (
            "old_password" in request.POST
            or "new_password1" in request.POST
            or "new_password2" in request.POST
        ):
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keep user logged in
                messages.success(request, "Your password has been changed successfully")
                return redirect("profile")
            else:
                messages.error(request, "Please correct the error below.")

        elif "first_name" in request.POST or "last_name" in request.POST:
            try:
                customer_profile_instance = request.user.customerprofile
                customer_profile_form = CustomerProfileUpdateForm(
                    request.POST, instance=customer_profile_instance
                )
            except ObjectDoesNotExist:
                customer_profile_form = CustomerProfileUpdateForm(request.POST)

            if customer_profile_form.is_valid():
                customer_profile_form.save()
                messages.success(
                    request, "Your customer profile has been updated successfully"
                )
                return redirect("profile")
            else:
                messages.error(request, "Please correct the error below.")

        context = {
            "user_form": user_form,
            "profile_form": profile_form,
            "password_form": password_form,
            "customer_profile_form": customer_profile_form,
        }

        return render(request=request, template_name="profile.html", context=context)


def clear_messages(request):
    storage = messages.get_messages(request)
    storage.used = True


class LoginView(AuthLoginView):
    template_name = "login.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        login(
            self.request,
            form.get_user(),
            backend="django.contrib.auth.backends.ModelBackend",
        )

        clear_messages(self.request)
        messages.success(self.request, "Login successful.")
        logger.info(f"User {form.get_user().username} logged in successfully.")

        user = form.get_user()
        try:
            user.customerprofile
        except ObjectDoesNotExist:
            logger.info(f"User {user.username} does not have a customer profile.")

        return super().form_valid(form)

    def form_invalid(self, form):
        clear_messages(self.request)
        messages.error(
            self.request, "Login failed. Please check your username and password."
        )
        logger.warning(f"Login attempt failed for user {form.data.get('username')}.")
        return super().form_invalid(form)


class RegisterView(FormView):
    template_name = "register.html"
    form_class = UserClientCreationForm
    success_url = reverse_lazy("personal_information")

    def form_valid(self, form):
        try:
            user, employeeGroups = form.save()

            # Ensure customer profile exists and is marked as an employee
            self.ensure_customer_profile(user)

            # Use the ModelBackend explicitly for login
            login(
                self.request, user, backend="django.contrib.auth.backends.ModelBackend"
            )

            # Trigger document assignment to the user
            self.assign_documents_to_user(user)

            # Send note to the user to check documents
            self.send_document_note_to_user(user)

            clear_messages(self.request)  # Clear all existing messages
            messages.success(self.request, "Registration successful.")
            return super().form_valid(form)
        except NoPlandayEmailException:
            form.add_error(
                "email", "Provided E-Mail does not match any existing Planday E-Mail."
            )
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            form.add_error(None, "Unsuccessful registration. Invalid information.")
        return self.form_invalid(form)

    def form_invalid(self, form):
        clear_messages(self.request)
        messages.error(
            self.request, "Form is not valid. Please correct the errors below."
        )
        return super().form_invalid(form)

    def ensure_customer_profile(self, user):
        customer_profile, created = CustomerProfile.objects.get_or_create(user=user)
        if created:
            customer_profile.is_employee = True
            customer_profile.save()

    def assign_documents_to_user(self, user):
        try:
            employee_profile = user.employeeprofile
            auto_assign_documents = Document.objects.filter(
                auto_assign_new_employees=True
            )
            for document in auto_assign_documents:
                document.assigned_employees.add(employee_profile)
            logger.info(f"Documents assigned to user {user.username}.")
        except EmployeeProfile.DoesNotExist:
            logger.error(f"Employee profile does not exist for user: {user.username}")

    def send_document_note_to_user(self, user):
        try:
            admin_user = User.objects.get(id=6)
            documents_link = self.request.build_absolute_uri(reverse("documents_list"))
            clickable_link = f'<a class="docs__link" href="{documents_link}">Link: View Documents</a>'
            note_content = (
                f"Please review and sign the required documents. {clickable_link}"
            )

            # Create a note with admin_user as the sender
            note = Note.objects.create(
                sender=admin_user,
                content=note_content,
            )
            note.receivers.add(user)

            # Set NoteReadStatus for the user to 'not read yet'
            NoteReadStatus.objects.create(note=note, user=user, is_read=False)
        except User.DoesNotExist:
            logger.error("Admin user with id=6 does not exist.")
        except Exception as e:
            logger.error(
                f"Failed to send document note to user {user.username}: {str(e)}"
            )

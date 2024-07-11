from base64 import b64encode
from io import BytesIO

import qrcode
from allauth.account.models import EmailAddress
from allauth.account.views import (
    ConfirmEmailView,
    LoginView,
    LogoutView,
    SignupView,
    login,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from customers.forms import CustomLoginForm, CustomSignupForm
from customers.models import CustomerProfile
from lib.pos_hello_tess import get_card_id_from_user

# from allauth.account.utils import send_email_confirmation


# def send_verification_email(user, request):
#     pass


class CustomerLoginView(LoginView):
    template_name = "account/customers_auth.html"
    success_url = reverse_lazy("customer_index")

    def get_form_class(self):
        return CustomLoginForm

    def form_valid(self, form):
        login(self.request, form.user)
        user = form.user

        # Set session expiry
        if form.cleaned_data["remember"]:
            self.request.session.set_expiry(60 * 60 * 24 * 365)  # 1 year
        else:
            self.request.session.set_expiry(43200)  # 12 hours

        # check if email is verified
        if EmailAddress.objects.filter(user=user, verified=True).exists():
            return JsonResponse({"success": True, "redirectUrl": self.success_url})
        else:
            # redirect to verify-email url if it's not verified
            verify_url = reverse(
                "verify_email", kwargs={"key": "key"}
            )  # TODO: get the correct key
            return JsonResponse({"success": True, "redirectUrl": verify_url})

    def form_invalid(self, form):
        errors = form.errors.as_json()
        return JsonResponse({"success": False, "errors": errors}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_state"] = self.request.GET.get("form", "login")
        context["is_login"] = True
        context["form_login"] = kwargs.get("form", self.get_form_class()())
        context["form_signup"] = SignupView.form_class()
        return context


@method_decorator(csrf_exempt, name="dispatch")
class CustomerSignupView(SignupView):
    """View to handle customer sign up."""

    template_name = "account/customers_auth.html"
    success_url = reverse_lazy("customer_index")

    def get_form_class(self):
        """Return the form class to use in this view."""
        return CustomSignupForm

    def form_valid(self, form):
        """Validate form, save user and return appropriate JsonResponse."""
        email = form.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            form.add_error(
                None,
                ValidationError(
                    "An account with this email address already exists. "
                    "Please use the password recovery procedure if you forgot your password.",
                    code="email_exists",
                ),
            )
            return self.form_invalid(form)

        super().form_valid(form)
        return JsonResponse({"success": True})

    def form_invalid(self, form):
        """Return JsonResponse with errors when form is invalid."""
        errors = form.errors.as_json()
        return JsonResponse({"success": False, "errors": errors}, status=400)

    def get_context_data(self, **kwargs):
        """Return the context data for this view."""
        context = super().get_context_data(**kwargs)
        context["is_login"] = False
        context["form_signup"] = kwargs.get("form", self.get_form_class()())
        context["form_login"] = LoginView.form_class()
        return context


class CustomLogoutView(LogoutView):
    template_name = "account/logout.html"


def generate_qr_code_base64(data: str) -> str:
    # Generate qr code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Remove bg
    img = qr.make_image(fill_color="black", back_color="transparent")

    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded_img = b64encode(buffer.read()).decode()

    return f"data:image/png;base64,{encoded_img}"


class CustomerIndexView(LoginRequiredMixin, TemplateView):
    template_name = "customers_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_profile = get_object_or_404(CustomerProfile, user=self.request.user)

        # Check if code is already stored in db, if not - create it
        if not customer_profile.card_qr_code:
            qr_code_data = generate_qr_code_base64(
                get_card_id_from_user(self.request.user)
            )
            customer_profile.card_qr_code = qr_code_data
            customer_profile.save()
        else:
            qr_code_data = customer_profile.card_qr_code

        # Add qr to context
        context["qr_code_data"] = qr_code_data

        return context


class CustomerEmailVerificationView(ConfirmEmailView):
    template_name = "account/verification_sent.html"

    def get(self, request, *args, **kwargs):
        self.key = kwargs.get("key")
        return super().get(request, *args, **kwargs)

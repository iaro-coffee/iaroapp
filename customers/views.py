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
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from customers.forms import CustomLoginForm, CustomSignupForm
from customers.models import CustomerProfile

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
    template_name = "account/customers_auth.html"
    success_url = reverse_lazy("customer_index")

    def get_form_class(self):
        return CustomSignupForm

    def form_valid(self, form):
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
        errors = form.errors.as_json()
        return JsonResponse({"success": False, "errors": errors}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_login"] = False
        context["form_signup"] = kwargs.get("form", self.get_form_class()())
        context["form_login"] = LoginView.form_class()
        return context


class CustomLogoutView(LogoutView):
    template_name = "account/logout.html"


class CustomerIndexView(LoginRequiredMixin, TemplateView):
    template_name = "customers_index.html"

    # todo add qr-code data
    # qr_code_img = qrcode.make(get_card_id_from_user(instance.user))  # This should be the device for which you want to generate the QR code
    # buffer = BytesIO()
    # qr_code_img.save(buffer)
    # buffer.seek(0)
    # encoded_img = b64encode(buffer.read()).decode()
    # qr_code_data = f'data:image/png;base64,{encoded_img}' # send this to index

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            first_name = self.request.user.customerprofile.first_name
            if not first_name:
                first_name = "Guest"
        except CustomerProfile.DoesNotExist:
            first_name = "Guest"
        context["first_name"] = first_name
        return context


class CustomerEmailVerificationView(ConfirmEmailView):
    template_name = "account/verification_sent.html"

    def get(self, request, *args, **kwargs):
        self.key = kwargs.get("key")
        return super().get(request, *args, **kwargs)

from allauth.account.views import LoginView, SignupView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from customers.forms import CustomLoginForm, CustomSignupForm
from customers.models import CustomerProfile


class CustomerLoginView(LoginView):
    template_name = 'account/customers_auth.html'
    success_url = reverse_lazy('customer_index')

    def get_form_class(self):
        return CustomLoginForm

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['form_login'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_login'] = True
        context['form_login'] = kwargs.get('form', self.get_form_class()())
        context['form_signup'] = SignupView.form_class()
        print(context)
        return context


class CustomerSignupView(SignupView):
    template_name = 'account/customers_auth.html'
    success_url = reverse_lazy('customer_index')

    def get_form_class(self):
        return CustomSignupForm

    def form_valid(self, form):
        response = super().form_valid(form)
        email = form.cleaned_data['email']
        return HttpResponseRedirect(f"{reverse_lazy('account_email_verification_sent')}?email={email}")

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['form_signup'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_login'] = False
        context['form_signup'] = kwargs.get('form', self.get_form_class()())
        context['form_login'] = LoginView.form_class()()
        return context


class CustomLogoutView(LogoutView):
    template_name = 'account/logout.html'


class CustomerIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'customers_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            first_name = self.request.user.customerprofile.first_name
            if not first_name:
                first_name = 'Guest'
        except CustomerProfile.DoesNotExist:
            first_name = 'Guest'
        context['first_name'] = first_name
        return context


from allauth.account.views import LoginView, SignupView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from customers.forms import CustomLoginForm


class CustomerLoginView(LoginView):
    template_name = 'account/customers_auth.html'
    success_url = reverse_lazy('index')

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
    success_url = reverse_lazy('index')

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

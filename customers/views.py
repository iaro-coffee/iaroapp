from allauth.account.views import LoginView, SignupView
from django.urls import reverse_lazy
from customers.forms import CustomLoginForm

class UserLoginView(LoginView):
    template_name = 'account/login_signup.html'
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
        return context


class UserSignupView(SignupView):
    template_name = 'account/login_signup.html'
    success_url = reverse_lazy('index')

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['form_signup'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_login'] = False
        context['form_signup'] = kwargs.get('form', self.get_form_class()())
        return context

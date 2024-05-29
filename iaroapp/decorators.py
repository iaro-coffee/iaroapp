from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

from customers.models import CustomerProfile


def employee_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            if not request.user.customerprofile.is_employee:
                return redirect('access_denied')
        except CustomerProfile.DoesNotExist:
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

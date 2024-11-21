from django.shortcuts import redirect
from django.urls import reverse

from customers.models import CustomerProfile
from employees.models import EmployeeProfile


class OnboardingCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Exempt admin users from redirection
            if request.user.is_superuser:
                return self.get_response(request)

            try:
                # check if user is an employee
                customer_profile = request.user.customerprofile
                if (
                    customer_profile.is_employee == 1
                ):  # Only proceed if marked as an employee
                    employee_profile = request.user.employeeprofile
                    if not employee_profile.onboarding_stages.get(
                        "personal_information", False
                    ):
                        if request.path != reverse("onboarding:personal_information"):
                            return redirect("onboarding:personal_information")
                else:
                    # Exempt users with is_employee=0 from redirection
                    return self.get_response(request)

            except (CustomerProfile.DoesNotExist, EmployeeProfile.DoesNotExist):
                # Exempt users without employee profiles
                return self.get_response(request)

        response = self.get_response(request)
        return response

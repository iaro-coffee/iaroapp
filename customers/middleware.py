from django.shortcuts import redirect

from customers.models import CustomerProfile


class RestrictAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            if request.user.is_authenticated:
                try:
                    customer_profile = CustomerProfile.objects.get(user=request.user)
                    if not customer_profile.is_employee:
                        # Redirect back to the previous page or homepage
                        return redirect(request.headers.get("referer", "/"))
                except CustomerProfile.DoesNotExist:
                    # If the customer profile does not exist, restrict access
                    return redirect(request.headers.get("referer", "/"))

        response = self.get_response(request)
        return response

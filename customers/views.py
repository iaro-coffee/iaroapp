from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerProfileUpdateForm
from .models import CustomerProfile


# @login_required
# def update_customer_profile(request):
#     try:
#         customer_profile = request.user.customerprofile
#     except CustomerProfile.DoesNotExist:
#         customer_profile = CustomerProfile(user=request.user)
#
#     if request.method == 'POST':
#         form = CustomerProfileUpdateForm(request.POST, instance=customer_profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Your customer profile has been updated successfully.')
#             return redirect('update_customer_profile')
#         else:
#             messages.error(request, 'Please correct the error below.')
#     else:
#         form = CustomerProfileUpdateForm(instance=customer_profile)
#
#     context = {
#         'form': form
#     }
#     return render(request, 'customers/update_customer_profile.html', context)

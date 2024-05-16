from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, reverse
from django.views import View


class Profile(LoginRequiredMixin, View):
    def get(self, request):
        # user_form = UserUpdateForm(instance=request.user)
        # profile_form = ProfileUpdateForm(instance=request.user.profile)

        # context = {
        #    'user_form': user_form,
        #    'profile_form': profile_form
        # }
        context = {}

        return render(request, "users/profile.html", context)

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(request, "Your profile has been updated successfully")

            return redirect("profile")
        else:
            context = {"user_form": user_form, "profile_form": profile_form}
            messages.error(request, "Error updating you profile")

            return render(request, "users/profile.html", context)

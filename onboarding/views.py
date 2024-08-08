from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from .forms import PersonalInformationForm


class PersonalInformationView(View):
    template_name = "personal_information.html"

    def get(self, request):
        form = PersonalInformationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PersonalInformationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Your information has been submitted successfully."
            )
            return redirect("index")
        else:
            messages.warning(request, "Please correct the errors below.")
        return render(request, self.template_name, {"form": form})

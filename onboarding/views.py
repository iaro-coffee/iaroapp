import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from lib.zoho import (
    generate_access_token,
    get_embedded_signing_url,
    get_template_details,
    send_document_using_template,
)

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


def sign_document(request):
    try:
        # Step 1: Generate Access Token
        access_token = generate_access_token()
        print(f"Access Token: {access_token}")  # Debugging access token generation

        # Step 2: Get Template Details
        template_id = "66746000000038081"  # Replace with your template ID
        template_details = get_template_details(template_id, access_token)
        print(
            f"Template Details: {json.dumps(template_details, indent=4)}"
        )  # Debugging template details

        # Step 3: Send Document Using Template (without pre-filling fields)
        recipient_email = "3dom.ua@gmail.com"  # Replace with actual recipient email
        recipient_name = "John Doe"  # Replace with actual recipient name
        send_response = send_document_using_template(
            template_id, template_details, recipient_email, recipient_name, access_token
        )
        print(
            "Send Response:", json.dumps(send_response, indent=4)
        )  # Debugging send_response

        # Step 4: Extract request_id and action_id
        request_id = send_response.get("requests", {}).get("request_id")
        print(f"Extracted Request ID: {request_id}")  # Debugging extracted request_id

        actions = send_response.get("requests", {}).get("actions", [])
        if not actions:
            print("No actions found in the response.")
            raise ValueError("No actions found in the response.")

        action_id = actions[0].get("action_id")
        print(f"Extracted Action ID: {action_id}")  # Debugging extracted action_id

        # Debugging: Print the request_id and action_id to inspect them
        print(f"Request ID: {request_id}, Action ID: {action_id}")

        if not request_id or not action_id:
            raise ValueError("request_id or action_id is None, cannot proceed.")

        # Step 5: Get Embedded Signing URL with correct domain
        signing_url = get_embedded_signing_url(
            request_id, action_id, "app.iaro.co", access_token
        )
        print(f"Signing URL: {signing_url}")  # Debugging signing URL

        # Render the signing page with the iframe
        return render(request, "sign_document.html", {"signing_url": signing_url})

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return JsonResponse({"error": str(e)})

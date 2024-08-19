from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from lib.zoho import (
    check_document_status,
    generate_access_token,
    get_embedded_signing_url,
    get_template_details,
    send_document_using_template,
)

from .forms import PersonalInformationForm
from .models import Document, SignedDocument


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


class DocumentSignView(View):
    template_name = "document_sign.html"

    def get(self, request, document_id):
        try:
            user = request.user
            document = get_object_or_404(Document, id=document_id)

            # Check if a signing process has already been started by this user
            signed_document = SignedDocument.objects.filter(
                user=user, document_id=document_id
            ).first()

            if signed_document:
                # Reuse the existing document and regenerate the signing URL
                request_id = signed_document.request_id
                action_id = signed_document.action_id
                access_token = generate_access_token()

                # Check the status of the document
                request_status = check_document_status(request_id, access_token)

                if request_status is None:
                    request_status = "unknown"  # Fallback if status is None

                # Always regenerate the signing URL, even if completed
                try:
                    signing_url = get_embedded_signing_url(
                        request_id,
                        action_id,
                        "8109-2a00-20-3013-a636-f287-a754-7591-3ee.ngrok-free.app",
                        access_token,
                    )
                    signed_document.signing_url = signing_url
                    signed_document.signing_status = request_status
                    signed_document.save()

                    # Render the document for viewing or signing based on status
                    context = {"pageTitle": document.name, "signing_url": signing_url}
                    return render(request, self.template_name, context)

                except Exception as e:
                    context = {
                        "pageTitle": "Error Signing",
                        "message": f"{request_status.capitalize()} of document failed with error: {str(e)}",
                    }
                    return render(request, self.template_name, context)

            else:
                # No previous signing process found, generate a new signing process
                access_token = generate_access_token()
                template_id = document.template_id
                template_details = get_template_details(template_id, access_token)

                # Send the document using the template (Consumes 1 API Quota)
                send_response = send_document_using_template(
                    template_id,
                    template_details,
                    user.email,
                    f"{user.first_name} {user.last_name}",
                    access_token,
                )

                request_id = send_response["request_id"]
                action_id = send_response["action_id"]

                # Get the embedded signing URL
                signing_url = get_embedded_signing_url(
                    request_id,
                    action_id,
                    "8109-2a00-20-3013-a636-f287-a754-7591-3ee.ngrok-free.app",
                    access_token,
                )

                # Save the new signing URL and status in the database
                SignedDocument.objects.create(
                    user=user,
                    document_id=document_id,
                    signing_url=signing_url,
                    request_id=request_id,
                    action_id=action_id,
                    signing_status="in_progress",
                )

            # Render the signing page with the iframe
            context = {"pageTitle": "Sign Document", "signing_url": signing_url}
            return render(request, self.template_name, context)

        except Exception as e:
            return JsonResponse({"error": str(e)})


class DocumentsListView(View):
    template_name = "documents_list.html"

    def get(self, request):
        documents = Document.objects.all()
        user = request.user

        for document in documents:
            signed_document = SignedDocument.objects.filter(
                user=user, document=document
            ).first()
            document.signing_status = (
                signed_document.signing_status if signed_document else "not_started"
            )

        context = {
            "pageTitle": "Documents List",
            "documents": documents,
        }
        return render(request, self.template_name, context)

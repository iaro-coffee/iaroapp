import gc
import os

import psutil
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls.base import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from pdf2image import convert_from_path, pdfinfo_from_path

from employees.models import EmployeeProfile
from inventory.models import Branch

from .forms import NoteForm, PDFUploadForm, VideoUploadForm
from .models import (
    LearningCategory,
    Note,
    NoteReadStatus,
    PDFCompletion,
    PDFImage,
    PDFUpload,
    Video,
)


class NoteView(LoginRequiredMixin, TemplateView):
    template_name = "view_notes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = NoteForm(initial={"user": self.request.user})

        user = self.request.user
        user_branch = user.employeeprofile.branch

        # Fetch received notes (combine by user and by user's branch) - init load, first 5
        received_notes = (
            Note.objects.filter(Q(receivers=user) | Q(branches=user_branch))
            .distinct()
            .order_by("-timestamp")[:4]
        )

        # Mark notes as read for the current user
        for note in received_notes:
            read_status, created = NoteReadStatus.objects.get_or_create(
                note=note, user=user
            )
            if not read_status.is_read:
                read_status.is_read = True
                read_status.save()

        # Fetch sent notes
        sent_notes = self.request.user.sent_notes.all().order_by("-timestamp")[:4]

        context["received_notes"] = received_notes
        context["sent_notes"] = sent_notes
        context["pageTitle"] = "Notes"
        return context

    def post(self, request, *args, **kwargs):
        form = NoteForm(request.POST, initial={"user": request.user})
        if form.is_valid():
            note = form.save(commit=False, sender=request.user)

            # Handle document assignment if a document is attached
            documents = form.cleaned_data.get("document")
            if documents:
                # Generate the link to the documents list
                documents_link = request.build_absolute_uri(reverse("documents_list"))
                clickable_link = f'<a class="docs__link" href="{documents_link}">Link: View Documents</a>'

                # Append the clickable link to the note content
                note.content += f" {clickable_link}"

            # Save the note with the updated content
            note.save()
            form.save_m2m()

            if documents:
                receivers = form.cleaned_data.get("receivers")
                branches = form.cleaned_data.get("branches")
                all_recipients = set(receivers)

                # Add all users in the specified branches
                for branch in branches:
                    all_recipients.update(
                        User.objects.filter(employeeprofile__branch=branch)
                    )

                # Assign each document to the corresponding employee profiles
                for document in documents:
                    for recipient in all_recipients:
                        employee_profile = recipient.employeeprofile
                        document.assigned_employees.add(employee_profile)

            # Create NoteReadStatus entries for each recipient
            receivers = form.cleaned_data["receivers"]
            branches = form.cleaned_data["branches"]
            all_recipients = set(receivers)

            # Add all users in the specified branches
            for branch in branches:
                all_recipients.update(
                    User.objects.filter(employeeprofile__branch=branch)
                )

            for recipient in all_recipients:
                NoteReadStatus.objects.create(note=note, user=recipient, is_read=False)

            return redirect("view_notes")
        else:
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)


class LoadMoreNotesView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        offset = int(request.GET.get("offset", 0))
        limit = 5
        user = request.user
        user_branch = user.employeeprofile.branch

        received_notes = list(
            Note.objects.filter(Q(receivers=user) | Q(branches=user_branch))
            .distinct()
            .order_by("-timestamp")[offset : offset + limit]
        )

        sent_notes = list(
            user.sent_notes.all().order_by("-timestamp")[offset : offset + limit]
        )

        data = {
            "received_notes": [
                self.note_to_dict(note, user_branch) for note in received_notes
            ],
            "sent_notes": [self.note_to_dict(note, user_branch) for note in sent_notes],
        }

        return JsonResponse(data)

    def note_to_dict(self, note, user_branch):
        local_time = timezone.localtime(note.timestamp)
        return {
            "sender_first_name": (
                note.sender.employeeprofile.first_name
                if note.sender and hasattr(note.sender, "employeeprofile")
                else None
            ),
            "sender_last_name": (
                note.sender.employeeprofile.last_name
                if note.sender and hasattr(note.sender, "employeeprofile")
                else None
            ),
            "sender_username": note.sender.username if note.sender else None,
            "sender_avatar": (
                note.sender.employeeprofile.avatar.url
                if note.sender and note.sender.employeeprofile.avatar
                else ""
            ),
            "content": note.content,
            "timestamp_date": local_time.strftime("%B %d"),
            "timestamp_time": local_time.strftime("%H:%M"),
            "branches": (
                [{"name": branch.name} for branch in note.branches.all()]
                if note.branches.exists()
                else None
            ),
            "receivers": (
                [
                    {
                        "username": receiver.username,
                        "first_name": (
                            receiver.employeeprofile.first_name
                            if hasattr(receiver, "employeeprofile")
                            else None
                        ),
                        "last_name": (
                            receiver.employeeprofile.last_name
                            if hasattr(receiver, "employeeprofile")
                            else None
                        ),
                        "avatar": (
                            receiver.employeeprofile.avatar.url
                            if receiver.employeeprofile.avatar
                            else None
                        ),
                    }
                    for receiver in note.receivers.all()
                ]
                if note.receivers.exists()
                else None
            ),
        }


class UnreadCountView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        user_branch = user.employeeprofile.branch

        unread_count = NoteReadStatus.objects.filter(
            Q(user=user)
            & Q(is_read=False)
            & (Q(note__receivers=user) | Q(note__branches=user_branch))
        ).count()

        return JsonResponse({"unread_count": unread_count})


class VideoUploadView(View):
    def get(self, request):
        form = VideoUploadForm()
        return render(request, "upload_video.html", {"form": form})

    def post(self, request):
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("view_videos")
        return render(request, "upload_video.html", {"form": form})


class VideoListView(View):
    def get(self, request):
        categories = Video.objects.values_list("category", flat=True).distinct()
        videos_by_category = {
            category: Video.objects.filter(category=category) for category in categories
        }

        return render(
            request, "video_list.html", {"videos_by_category": videos_by_category}
        )


conversion_status = {"current_page": 0, "memory_usage": 0.0, "total_pages": 0}


def upload_pdf(request):
    categories = LearningCategory.objects.all()
    branches = Branch.objects.all()

    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)
        new_category_name = request.POST.get("new_category")

        if new_category_name:
            category, created = LearningCategory.objects.get_or_create(
                name=new_category_name
            )
            post_data = request.POST.copy()
            post_data["category"] = category.id
            form = PDFUploadForm(post_data, request.FILES)

        if form.is_valid():
            pdf_upload = form.save(commit=False)
            pdf_upload.file = request.FILES["file"]
            pdf_upload.save()
            form.save_m2m()

            pdf_path = pdf_upload.file.path
            try:
                batch_size = 3
                conversion_status["total_pages"] = pdfinfo_from_path(pdf_path).get(
                    "Pages", 0
                )
                conversion_status["current_page"] = 0
                total_pages = 0

                while True:
                    try:
                        images = convert_from_path(
                            pdf_path,
                            first_page=total_pages + 1,
                            last_page=total_pages + batch_size,
                            dpi=150,
                            thread_count=2,
                            use_pdftocairo=True,
                            fmt="jpeg",
                        )
                        if not images:
                            break

                        for i, image in enumerate(images):
                            page_number = total_pages + i + 1
                            image_filename = f"{pdf_upload.id}_{page_number}.jpg"
                            image_path = os.path.join(
                                settings.MEDIA_ROOT, "pdf_images", image_filename
                            )
                            image.save(image_path, "JPEG")
                            PDFImage.objects.create(
                                pdf=pdf_upload,
                                image=f"pdf_images/{image_filename}",
                                page_number=page_number,
                            )

                            conversion_status["current_page"] = page_number
                            image.close()
                            del image
                            gc.collect()

                        total_pages += len(images)
                        process = psutil.Process(os.getpid())
                        mem_info = process.memory_info()
                        conversion_status["memory_usage"] = mem_info.rss / (1024 * 1024)

                    except Exception as e:
                        messages.error(
                            request,
                            f"Error converting pages {total_pages + 1} to {total_pages + batch_size}: {e}",
                        )
                        break

                messages.success(
                    request, f"Successfully uploaded and converted {total_pages} pages."
                )
                return JsonResponse(
                    {
                        "success": True,
                        "redirect_url": redirect(
                            "view_slides", pdf_id=pdf_upload.id
                        ).url,
                    }
                )

            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
                return JsonResponse(
                    {"success": False, "error": f"An unexpected error occurred: {e}"}
                )

        else:
            errors = {
                field: error.get_json_data() for field, error in form.errors.items()
            }
            return JsonResponse({"success": False, "errors": errors})

    else:
        form = PDFUploadForm()

    return render(
        request,
        "upload_pdf.html",
        {
            "form": form,
            "categories": categories,
            "branches": branches,
            "pageTitle": "PDF Upload",
        },
    )


def get_conversion_details(request):
    if request.method == "POST" and request.FILES.get("file"):
        pdf_file = request.FILES["file"]
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, pdf_file.name)

        with open(pdf_path, "wb+") as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        file_size = os.path.getsize(pdf_path) / (1024 * 1024)

        try:
            pdf_info = pdfinfo_from_path(pdf_path)
            total_pages = pdf_info.get("Pages", 0)
        except Exception as e:
            print(f"An error occurred while getting PDF info: {e}")
            total_pages = 0

        os.remove(pdf_path)

        return JsonResponse(
            {"file_size": round(file_size, 2), "total_pages": total_pages}
        )

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_conversion_status(request):
    if request.method == "GET":
        return JsonResponse(conversion_status)
    return JsonResponse({"error": "Invalid request"}, status=400)


def view_slides(request, pdf_id):
    pdf = get_object_or_404(PDFUpload, id=pdf_id)
    pdf_images = PDFImage.objects.filter(pdf=pdf).order_by("page_number")

    # Check if the current user has marked this PDF as completed
    completed = PDFCompletion.objects.filter(user=request.user, pdf=pdf).exists()

    return render(
        request,
        "view_slides.html",
        {
            "pdf_images": pdf_images,
            "pdf": pdf,
            "pageTitle": "PDF Education Details",
            "completed": completed,
        },
    )


def view_slides_list(request):
    selected_branch = request.GET.get("branch", "All")

    branches = Branch.objects.values_list("name", flat=True)

    if selected_branch == "All":
        branch_filter = Q()
    else:
        branch_filter = Q(branches__name=selected_branch)

    # Use LearningCategory objects as keys
    pdfs_by_category = {
        category: PDFUpload.objects.filter(category=category).filter(branch_filter)
        for category in LearningCategory.objects.all()
    }

    # Filter out categories that do not have any PDFs
    pdfs_by_category = {
        category: pdfs for category, pdfs in pdfs_by_category.items() if pdfs.exists()
    }

    # Check which PDFs the user has completed
    completed_pdfs = PDFCompletion.objects.filter(user=request.user).values_list(
        "pdf_id", flat=True
    )

    # Determine if all PDFs in each category are completed
    all_completed_categories = {
        category: all(pdf.id in completed_pdfs for pdf in pdfs)
        for category, pdfs in pdfs_by_category.items()
    }

    # Calculate completion percentage for each category
    completion_percentages = {}
    for category, pdfs in pdfs_by_category.items():
        total_pdfs = pdfs.count()
        completed_count = sum(1 for pdf in pdfs if pdf.id in completed_pdfs)
        completion_percentage = (
            (completed_count / total_pdfs * 100) if total_pdfs > 0 else 0
        )
        completion_percentages[category] = completion_percentage

    return render(
        request,
        "view_slides_list.html",
        {
            "pageTitle": "PDF Education List",
            "pdfs_by_category": pdfs_by_category,
            "branches": branches,
            "selected_branch": selected_branch,
            "completed_pdfs": completed_pdfs,
            "all_completed_categories": all_completed_categories,
            "completion_percentages": completion_percentages,
        },
    )


class MarkPDFCompleteView(View):
    def post(self, request, *args, **kwargs):
        pdf_id = request.POST.get("pdf_id")
        pdf = get_object_or_404(PDFUpload, id=pdf_id)

        # Check if the user has already marked this PDF as complete
        if PDFCompletion.objects.filter(user=request.user, pdf=pdf).exists():
            messages.info(request, "You have already marked this Lesson as complete.")
        else:
            PDFCompletion.objects.create(user=request.user, pdf=pdf)
            messages.success(request, "Lesson marked as complete successfully.")

        return redirect("view_slides", pdf_id=pdf_id)


def is_superuser(user):
    return user.is_superuser


@user_passes_test(is_superuser)
def user_progress(request):
    branch_name = request.GET.get("branch", "All")
    branches = Branch.objects.all().values_list("name", flat=True)

    if branch_name == "All":
        selected_branch = "All"
        profiles = EmployeeProfile.objects.all()
        pdf_filter = {}
    else:
        try:
            branch = Branch.objects.get(name=branch_name)
            selected_branch = branch_name
            profiles = EmployeeProfile.objects.filter(branch=branch)
            pdf_filter = {"branches": branch}
        except Branch.DoesNotExist:
            profiles = EmployeeProfile.objects.none()
            pdf_filter = {}

    users = (
        User.objects.filter(employeeprofile__in=profiles)
        .prefetch_related("employeeprofile")
        .select_related("employeeprofile")
    )

    pdfs = PDFUpload.objects.filter(**pdf_filter)
    completed_pdfs = set(
        PDFCompletion.objects.filter(user=request.user).values_list("pdf_id", flat=True)
    )

    pdfs_by_user = {
        user.id: list(pdfs.filter(branches=user.employeeprofile.branch))
        for user in users
    }
    pdf_completions_by_user = {
        user.id: set(
            PDFCompletion.objects.filter(user=user).values_list("pdf_id", flat=True)
        )
        for user in users
    }

    context = {
        "pageTitle": "Employee Progress",
        "users": users,
        "pdfs_by_user": pdfs_by_user,
        "pdf_completions_by_user": pdf_completions_by_user,
        "completed_pdfs": completed_pdfs,
        "branches": branches,
        "selected_branch": selected_branch,
    }

    return render(request, "user_learning_progress.html", context)

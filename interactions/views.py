import os

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from pdf2image import convert_from_path as pdf2image_convert_from_path

from .forms import NoteForm, PDFUploadForm, VideoUploadForm
from .models import LearningCategory, Note, NoteReadStatus, PDFImage, PDFUpload, Video


class NoteView(LoginRequiredMixin, TemplateView):
    template_name = "view_notes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = NoteForm()

        user = self.request.user
        user_branch = user.profile.branch

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
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False, sender=request.user)
            note.save()
            form.save_m2m()

            # Create NoteReadStatus entries for each recipient
            receivers = form.cleaned_data["receivers"]
            branches = form.cleaned_data["branches"]
            all_recipients = set(receivers)

            # Add all users in the specified branches
            for branch in branches:
                all_recipients.update(User.objects.filter(profile__branch=branch))

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
        user_branch = user.profile.branch

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
            "sender_username": note.sender.username if note.sender else None,
            "sender_avatar": (
                note.sender.profile.avatar.url
                if note.sender and note.sender.profile.avatar
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
                        "avatar": (
                            receiver.profile.avatar.url
                            if receiver.profile.avatar
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
        user_branch = user.profile.branch

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


def convert_from_path(pdf_path):
    """
    Convert a PDF file to a list of images, one for each page.
    """
    images = pdf2image_convert_from_path(pdf_path, dpi=300)
    return images


def upload_pdf(request):
    categories = LearningCategory.objects.all()

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

            pdf_path = pdf_upload.file.path
            images = convert_from_path(pdf_path)
            for i, image in enumerate(images):
                image_filename = f"{pdf_upload.id}_{i}.jpg"
                image_path = os.path.join(
                    settings.MEDIA_ROOT, "pdf_images", image_filename
                )
                image.save(image_path, "JPEG")
                PDFImage.objects.create(
                    pdf=pdf_upload,
                    image=f"pdf_images/{image_filename}",
                    page_number=i + 1,
                )
            return redirect("view_slides", pdf_id=pdf_upload.id)
        else:
            print("Form errors:", form.errors)
    else:
        form = PDFUploadForm()

    return render(request, "upload_pdf.html", {"form": form, "categories": categories})


def view_slides(request, pdf_id):
    pdf = get_object_or_404(PDFUpload, id=pdf_id)
    pdf_images = PDFImage.objects.filter(pdf=pdf).order_by("page_number")
    return render(request, "view_slides.html", {"pdf_images": pdf_images, "pdf": pdf})


def view_slides_list(request):
    selected_category = request.GET.get("category", "All")

    if selected_category == "All":
        pdfs_by_category = {
            category.name: PDFUpload.objects.filter(category=category)
            for category in LearningCategory.objects.all()
        }
    else:
        category = LearningCategory.objects.get(name=selected_category)
        pdfs_by_category = {category.name: PDFUpload.objects.filter(category=category)}

    categories = LearningCategory.objects.values_list("name", flat=True)
    return render(
        request,
        "view_slides_list.html",
        {
            "pageTitle": "PDF Education List",
            "pdfs_by_category": pdfs_by_category,
            "categories": categories,
            "selected_category": selected_category,
        },
    )

# from django.contrib import admin
#
# from .models import Note
#
#
# @admin.register(Note)
# class NoteAdmin(admin.ModelAdmin):
#     list_display = ("sender", "content", "timestamp")
#     search_fields = ("sender__username", "content")
import os

from django.contrib import admin

from .models import LearningCategory, PDFImage, PDFUpload, Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "video_size", "video_format")

    @admin.display(description="Size (MB)")
    def video_size(self, obj):
        if obj.video_file:
            return f"{obj.video_file.size / (1024 * 1024):.2f} MB"
        return "Not available format"

    @admin.display(description="Format")
    def video_format(self, obj):
        if obj.video_file:
            return os.path.splitext(obj.video_file.name)[-1].upper()
        return "Not available"


class PDFImageInline(admin.TabularInline):
    model = PDFImage
    extra = 0
    readonly_fields = ("image", "page_number")


@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ("file", "category", "uploaded_at")
    inlines = [PDFImageInline]

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def delete_model(self, request, obj):
        obj.delete()


admin.site.register(LearningCategory)

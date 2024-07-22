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

from .models import Video


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

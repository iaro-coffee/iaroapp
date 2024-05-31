from django.contrib.auth.models import User
from django.db import models
from PIL import Image

from inventory.models import Branch


def get_first_branch_id():
    return Branch.objects.first().id


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(
        default="profile_avatars/avatar.png",  # default avatar
        upload_to="profile_avatars",           # dir to store the image
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, default=get_first_branch_id)

    def __str__(self):
        return f"{self.user.username} Profile"

    def save(self, *args, **kwargs):
        # save the profile first
        super().save(*args, **kwargs)

        # resize and crop the image
        img = Image.open(self.avatar.path)
        max_size = (300, 300)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        if img.format == 'PNG':
            new_img = Image.new("RGBA", max_size, (255, 255, 255, 0))
            new_img.paste(img, (int((max_size[0] - img.size[0]) / 2), int((max_size[1] - img.size[1]) / 2)), img.convert("RGBA"))
            new_img.save(self.avatar.path)
        else:
            new_img = Image.new("RGB", max_size, (255, 255, 255))
            new_img.paste(img, (int((max_size[0] - img.size[0]) / 2), int((max_size[1] - img.size[1]) / 2)))
            new_img.save(self.avatar.path)

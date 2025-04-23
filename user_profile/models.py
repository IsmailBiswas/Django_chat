from django.contrib.auth import get_user_model
from django.db import models

from dchat_messages.models import DChatFile


class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    profile_picture = models.OneToOneField(
        DChatFile, blank=True, null=True, on_delete=models.CASCADE, related_name="profile_picture"
    )
    display_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return self.user.username

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from dchat_users.models import Verification
from user_profile.models import Profile

user = get_user_model()


@receiver(post_save, sender=user, dispatch_uid="user_verification_instance")
def create_verification(sender, instance, created, **kwargs):
    if created:
        Verification.objects.create(user=instance)
        Profile.objects.create(user=instance)

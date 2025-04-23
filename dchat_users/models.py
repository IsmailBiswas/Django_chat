import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def validate_username(value):
    # Ensure username is less than 90 characters
    MaxLengthValidator(limit_value=90)(value)
    MinLengthValidator(limit_value=4)(value)

    # Use regular expression to check for allowed characters
    if not re.match(r"^[a-zA-Z0-9\-\_\.]+$", value):
        raise ValidationError(
            _("Username can only contain ASCII alphanumerics, hyphens, underscores, or periods."),
            params={"value": value},
        )


class DchatUser(AbstractUser):
    username_validator = validate_username
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 90 characters or fewer. Letters, digits and ./-/_ only."),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    email = models.EmailField(_("email address"), unique=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class Verification(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        app_label = "dchat_users"

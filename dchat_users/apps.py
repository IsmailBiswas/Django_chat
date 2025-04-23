from django.apps import AppConfig


class DchatUsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dchat_users"

    def ready(self):
        from . import signals  # noqa

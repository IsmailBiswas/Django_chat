from django.apps import AppConfig


class DchatMessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dchat_messages"

    def ready(self) -> None:
        from . import signals  # noqa

        return super().ready()

from django.contrib.auth import get_user_model
from django.db import models


class Group(models.Model):
    owner = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=60, blank=False)

    def __str__(self):
        return self.name


class Connection(models.Model):
    """Clients are expected to establish a single WebSocket connection, and
    this Model is designed to store information regarding the specific channel
    group names that consumers should listen for.
    """

    CONNETION_STATUS = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("BLOCKED", "Blocked"),
        ("REJECTED", "Rejected"),
    ]

    CONNECTION_TYPE = [
        ("USER", "user"),
        ("GROUP", "Group"),
    ]

    connection_type = models.CharField(max_length=30, choices=CONNECTION_TYPE)
    user_initiator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True, related_name="initiator"
    )
    user_acceptor = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True, related_name="acceptor"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=30, choices=CONNETION_STATUS)
    initiator_unread_message_count = models.IntegerField(default=0)
    acceptor_unread_message_count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.user_initiator.username}-{self.user_acceptor.username}"


class DChatFile(models.Model):
    file = models.FileField(upload_to="%Y_%m_%d")
    file_name = models.CharField(max_length=100)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    token = models.CharField(max_length=100)


class Message(models.Model):
    message = models.TextField(blank=True, null=True)
    message_unique_id = models.CharField(max_length=100, blank=False, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="received_messages")
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="sent_messages")
    # attachment = models.FileField(upload_to="%Y_%m_%d_message", blank=True, null=True)
    attachment = models.OneToOneField(
        DChatFile, blank=True, null=True, on_delete=models.CASCADE, related_name="message_attachment"
    )
    is_group_message = models.BooleanField(default=False)
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.CASCADE)
    # attachment_access_token = models.CharField(null=True, max_length=100)
    # mime_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.message_unique_id

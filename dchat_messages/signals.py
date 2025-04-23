from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from dchat_messages.add_hmac import add_hmac

from .models import Message

channel_layer = get_channel_layer()


@receiver(post_save, sender=Message, weak=False)
def send_message(sender, instance, **kwargs):
    # Adds a property named "hmac" to the instance
    add_hmac(single_object=instance.attachment)

    is_attachment = bool(instance.attachment)
    file_path = instance.attachment.file.url if is_attachment else None
    attachment_access_token = instance.attachment.token if is_attachment else None
    hmac = instance.attachment.hmac if is_attachment else None
    exp_time = instance.attachment.exp_time if is_attachment else None
    mime_type = instance.attachment.mime_type if is_attachment else None
    file_name = instance.attachment.file_name if is_attachment else None

    # Generate the url for the file.

    data = {
        "type": "chat.message",
        "message_type": "chat_message",
        "is_attachment": is_attachment,
        "mime_type": mime_type,
        "message_unique_id": instance.message_unique_id,
        "access_token": attachment_access_token,
        "hmac": hmac,
        "exp_time": exp_time,
        "file_path": file_path,
        "file_name": file_name,
        "message": instance.message,
        "recipient": instance.recipient.username,
        "sender": instance.sender.username,
        "recipient_type": "group" if instance.is_group_message else "user",
    }

    async_to_sync(channel_layer.group_send)(f"{data['recipient_type']}_{data['recipient']}", data)

    # Send back to the sender, this makes easy to sync message/file between
    # multiple devices with same account. Also this assures the file is
    # stored successfully if sender sees the sent file.
    if instance.recipient.username != instance.sender.username:
        self_data = {**data, "recipient": data["sender"]}
        async_to_sync(channel_layer.group_send)(f"{data['recipient_type']}_{data['sender']}", self_data)

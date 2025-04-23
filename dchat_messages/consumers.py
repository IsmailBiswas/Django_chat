# chat/consumers.py
import json

from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q


class ChatConsumer(WebsocketConsumer):
    # Entries in this list will be used by the super class to handle group creation, connection and disconnection.
    groups = []

    def websocket_connect(self, message):
        """Overriding this to populate the `groups` list."""
        from dchat_messages.models import Connection

        if self.scope["user"].is_authenticated:
            # Get all groups where the user is accepted
            user_groups = Connection.objects.filter(
                (Q(user_initiator=self.scope["user"]) & Q(group__isnull=False) & Q(status="ACCEPTED"))
                | (Q(user_acceptor=self.scope["user"]) & Q(group__isnull=False) & Q(status="ACCEPTED"))
            )

            # Prefix `group_` to every group name to avoid name collision username
            group_names = {f"group_{connection.group.name}" for connection in user_groups}

            username = self.scope["user"].username
            # Prefix `user_` to every user to avoid name collision with group name
            user_channel_group_name = f"user_{username}"

            # Append all the user group names to the groups list
            self.groups = self.groups + list(group_names)

            # Append the user channel name to the group list
            self.groups.append(user_channel_group_name)
        return super().websocket_connect(message)

    def connect(self):
        if self.scope["user"].is_authenticated:
            self.accept()

    # Receive message from WebSocket
    def receive(self, text_data):
        ...

    # Receive message
    def chat_message(self, event):
        # Send message to WebSocket
        self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "message_type": event["message_type"],
                    "recipient": event["recipient"],
                    "recipient_type": event["recipient_type"],
                    "sender": event["sender"],
                    "is_attachment": event["is_attachment"],
                    "mime_type": event["mime_type"],
                    "file_path": event.get("file_path", None),
                    "file_name": event.get("file_name", None),
                    "message_unique_id": event.get("message_unique_id", None),
                    "access_token": event.get("access_token", None),
                    "hmac": event.get("hmac", None),
                    "exp_time": event.get("exp_time", None),
                }
            )
        )

    def connection_message(self, event):
        self.send(
            text_data=json.dumps(
                {
                    "message_type": event.get("message_type", None),
                    "recipient_type": event.get("recipient_type", None),
                    "sender_username": event.get("sender_username", None),
                    "sender_profile_picture_path": event.get("sender_profile_picture_path", None),
                    "token": event.get("token", None),
                    "hmac": event.get("hmac", None),
                    "exp_time": event.get("exp_time", None),
                }
            )
        )

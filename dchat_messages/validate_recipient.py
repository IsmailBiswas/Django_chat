from django.contrib.auth import get_user_model
from django.db.models import Model, Q


def is_valid_recipient(sender: Model, recipient: str, recipient_type: str) -> dict:
    connection_validity = {
        "error": [],
        "is_valid": False,
        "connection_object": None,
    }
    from dchat_messages.models import Connection, Group

    accepted_connections = Connection.objects.filter(
        (Q(user_initiator=sender) & Q(status="ACCEPTED")) | (Q(user_acceptor=sender) & Q(status="ACCEPTED"))
    )

    if recipient_type == "user":
        recipient_user_qs = get_user_model().objects.filter(username=recipient)
        # Check if a user with provided username exists in database
        if recipient_user_qs:
            recipient_user = recipient_user_qs.first()

            # Get the connection object where recipient is also present.
            if recipient_user == sender:
                connection = [
                    user_connection
                    for user_connection in accepted_connections
                    if user_connection.user_initiator == recipient_user
                    and user_connection.user_acceptor == recipient_user
                ]
            else:
                connection = [
                    user_connection
                    for user_connection in accepted_connections
                    if user_connection.user_initiator == recipient_user
                    or user_connection.user_acceptor == recipient_user
                ]

            if len(connection) > 0:
                # Update the message counter and store it in a key
                # variable, but don't commit changes to the DB yet.
                if connection[0].user_initiator == recipient_user:
                    connection[0].initiator_unread_message_count = connection[0].initiator_unread_message_count + 1
                else:
                    connection[0].acceptor_unread_message_count = connection[0].acceptor_unread_message_count + 1
                connection_validity["connection_object"] = connection[0]

                connection_validity["is_valid"] = True
                connection_validity["recipient_object"] = recipient_user
            else:
                connection_validity["error"].append("Requesting user is not connected with the recipient user")
        else:
            connection_validity["error"].append("Invalid recipient")

    elif recipient_type == "group":
        group_qs = Group.objects.filter(name=recipient)
        if group_qs:
            group = group_qs.first()
            if len([connection for connection in accepted_connections if connection.group == group]) > 0:
                connection_validity["is_valid"] = True
                connection_validity["recipient_object"] = group
            else:
                connection_validity["error"].append(
                    "Error: The user is either blocked in the requested group \
                    or has a pending group join request."
                )
        else:
            connection_validity["error"].append("Requested group does not exist")
    else:
        connection_validity["error"].append("Invalid recipient type")
    return connection_validity

import hashlib
import hmac
import secrets
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.views import View
from django.views.generic import ListView

from dchat_messages.add_hmac import add_hmac
from dchat_messages.models import Connection, DChatFile, Message
from dchat_messages.validate_recipient import is_valid_recipient


class UserList(ListView):
    """Returns a partial HTML content representing a list of connected users for
    the requesting user.
    """

    model = Connection
    paginate_by = 20
    template_name = "dchat_messages/connection_list.html"
    context_object_name = "users"

    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query_set = super().get_queryset()
        accepted_connections = query_set.filter(
            (Q(user_initiator=self.request.user) & Q(status="ACCEPTED") & Q(group__isnull=True))
            | (Q(user_acceptor=self.request.user) & Q(status="ACCEPTED") & Q(group__isnull=True))
        ).select_related("user_initiator", "user_acceptor")

        # Creates a list of tuple the first value in the tuple is the user
        # connected user and second value is the number of unread message for
        # that user
        connected_users = [
            (
                (connection.user_acceptor, connection.initiator_unread_message_count)
                if connection.user_initiator == self.request.user
                else (connection.user_initiator, connection.acceptor_unread_message_count)
            )
            for connection in accepted_connections
        ]

        # Create a new property for each user to store the unread message count.
        for user, unread_message_count in connected_users:
            user.unread_message_count = unread_message_count

        users = [user[0] for user in connected_users]

        file_objects = [tup[0].profile.profile_picture for tup in connected_users]

        add_hmac(file_objects)

        return users


class UserConnect(ListView):
    """Checks if requesting user is connected with requestee and send partial
    HTML response which contains chat history.
    """

    template_name = "dchat_messages/user_connection.html"
    model = Message
    context_object_name = "messages"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_exists = False
        if self.dchat_recipient_user and self.dchat_has_connection:
            user_exists = True
            context["connection"] = self.dchat_user_connection
        elif self.dchat_recipient_user and not self.dchat_has_connection:
            user_exists = True

        context["user_exists"] = user_exists
        # context["recipient_username"] = self.kwargs["username"]
        context["recipient_user"] = self.dchat_recipient_user
        return context

    def get_queryset(self, *args, **kwargs):
        queryset = Message.objects.none()
        recipient_user = get_user_model().objects.filter(username=self.kwargs["username"])
        self.dchat_recipient_user = recipient_user  # Will be used in `get_context_data`
        if recipient_user:
            recipient_user = recipient_user.first()
            add_hmac(single_object=recipient_user.profile.profile_picture)

            # Overrides queryset with single object
            self.dchat_recipient_user = recipient_user

            # check if they are connected
            connection = (
                Connection.objects.filter(
                    (Q(user_initiator=self.request.user) & Q(user_acceptor=recipient_user))
                    | (Q(user_acceptor=self.request.user) & Q(user_initiator=recipient_user))
                )
                .select_related("user_initiator", "user_acceptor")
                .first()
            )

            # Send an instance of `Connection` so that template can make
            # decision based on value in the `Connection` instance.
            if connection is not None:
                self.dchat_has_connection = True
                if connection.user_initiator == self.request.user:
                    connection.initiator_unread_message_count = 0
                else:
                    connection.acceptor_unread_message_count = 0
                connection.save()

                self.dchat_user_connection = connection  # Will be used in `get_context_data`
                if connection.status == "ACCEPTED":
                    # Get all the messages where current user is recipient for selected user.
                    queryset = (
                        Message.objects.filter(
                            (Q(recipient=self.request.user) & Q(sender=recipient_user))
                            | (Q(recipient=recipient_user) & Q(sender=self.request.user))
                        )
                        .select_related("recipient", "sender")
                        .order_by("-timestamp")
                    )
                    file_objects = [file_object.attachment for file_object in queryset]
                    # file_objects = [tup[0].profile.profile_picture for tup in connected_users]
                    add_hmac(iterable=file_objects)
            else:
                self.dchat_has_connection = False

        else:
            raise Http404("No objects found matching the specified criteria.")

        return queryset

    def get_template_names(self) -> list[str]:
        if self.request.GET.get("chat_history"):
            return "dchat_messages/chat_history.html"
        else:
            return "dchat_messages/user_connection.html"


class ReceiveMessage(View):
    """Handles file storage sent by client as message attachment"""

    def post(self, request, *args, **kwargs):
        # Check is request is authenticated.
        if request.user.is_authenticated:
            attachment = request.FILES.get("attachment", None)

            # file_name = request.POST.get("file_name", None) # Not needed
            # is_attachment = request.POST.get("is_attachment", None) # Not needed

            message = request.POST.get("message", None)
            message_unique_id = request.POST.get("message_unique_id", None)
            recipient_name = request.POST.get("recipient", None)
            recipient_type = request.POST.get("recipient_type", None)

            field_error = JsonResponse(
                {
                    "error": "Invalid fields",
                    "Required fields": [
                        "message_unique_id<UUID>",
                        "recipient<string>",
                        "recipient_type<string>",
                    ],
                    "optional fields": [
                        "message<string>",
                        "attachment<file>",
                    ],
                    "message": "Any one of optional field is required",
                },
                status=400,
            )

            if None in (message_unique_id, recipient_name, recipient_type):
                return field_error

            if message is None and attachment is None:
                return field_error
            if attachment is None and message == "":
                return JsonResponse(
                    {"error": "Message can not be empty when there is no attachment file."}, status=400
                )

            # connection_validity = get_user_model().objects.filter(username=recipient_name)
            connection_validity = is_valid_recipient(
                sender=self.request.user,
                recipient=recipient_name,
                recipient_type=recipient_type,
            )

            if not connection_validity["is_valid"]:
                return JsonResponse({"error": connection_validity["error"]}, status=400)

            else:
                # content_type = attachment.content_type if attachment else None

                if attachment:
                    attachment_object = DChatFile.objects.create(
                        file=attachment,
                        file_name=attachment.name,
                        mime_type=attachment.content_type,
                        token=secrets.token_urlsafe(),
                    )

                data = {
                    "sender": self.request.user,
                    "recipient": connection_validity["recipient_object"],
                    "message": message,
                    "message_unique_id": message_unique_id,
                    "attachment": attachment_object if attachment else None,
                }

                # lookup_params = {"message_unique_id": message_unique_id}

                try:
                    # The `transaction.atomic` context manager ensures the atomicity of the
                    # database transactions for both message storage and counter update.
                    # This guarantees that either both operations are executed successfully,
                    # or none of them are performed.
                    with transaction.atomic():
                        # Save the sent message in database.
                        Message.objects.create(**data)
                        connection_validity["connection_object"].save()

                        # Create file instance

                    return HttpResponse(status=201)
                except IntegrityError:
                    ...

        else:
            return JsonResponse({"error": "Request is not authorized"}, status=401)


class FileAccessAuth(View):
    def validate_request(self, token: str, req_file_path: str, provided_hmac: str, provided_exp_time: str) -> bool:
        # attachment_objects = DChatFile.objects.filter(token=token)

        try:
            int_exp_time = int(provided_exp_time)
        except ValueError:
            return False

        if int_exp_time < int(time.time()):
            return False

        secret_key = getattr(settings, "SECRET_KEY").encode("utf-8")
        data = f"/{req_file_path}_{token}_{provided_exp_time}".encode()

        # expiry_time = int(time.time()) + _expiry_time
        # data = f"{file_path}_{access_token}_{expiry_time}".encode("utf-8")

        hmac_obj = hmac.new(secret_key, data, hashlib.sha256)
        calculated_hex_digest = hmac_obj.hexdigest()
        is_hmac_match = hmac.compare_digest(calculated_hex_digest, provided_hmac)
        if is_hmac_match:
            return True
        else:
            return False

        # attachment_object = attachment_objects.first()
        # if attachment_objects:
        #     if attachment_object.attachment.url == f"/{req_file_path}":
        #         return True
        #     return False
        # else:
        #     return False

    def get(self, request):
        original_uri = request.headers.get("X-Original-URI")
        if original_uri:
            from urllib.parse import parse_qs, urlparse

            parsed_url = urlparse(original_uri)
            parameters = parse_qs(parsed_url.query)
            req_file_path = "/".join(parsed_url.path.split("/")[-2:])

            # Access the parameters
            token = parameters.get("token", None)
            provided_hmac = parameters.get("hmac", None)
            exp_time = parameters.get("exp_time", None)

            if token and hmac and exp_time:
                if self.validate_request(
                    token=token[0],
                    req_file_path=req_file_path,
                    provided_hmac=provided_hmac[0],
                    provided_exp_time=exp_time[0],
                ):
                    return HttpResponse(status=200)
                else:
                    return HttpResponse(status=401)
            else:
                return HttpResponse(status=401)

        else:
            return HttpResponse(status=401)


# Yes, it is still used after changing into AJAX to send messages
class MessageReadACK(View):
    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            sender_username = request.POST.get("sender", None)

            if sender_username is not None:
                sender_qs = get_user_model().objects.filter(username=sender_username)
                if not sender_qs:
                    return JsonResponse(
                        {
                            "error": f"User '{sender_username}' does not exists",
                        },
                        status=400,
                    )

                sender = sender_qs.first()

                connection = (
                    Connection.objects.filter(
                        (Q(user_initiator=self.request.user) & Q(user_acceptor=sender))
                        | (Q(user_acceptor=self.request.user) & Q(user_initiator=sender))
                    )
                    .select_related("user_initiator", "user_acceptor")
                    .first()
                )

                if connection.user_acceptor == self.request.user:
                    connection.acceptor_unread_message_count = 0
                else:
                    connection.initiator_unread_message_count = 0

                connection.save()
                return HttpResponse(status=200)

            else:
                return JsonResponse(
                    {
                        "error": "Bad Request",
                        "message": "The required fields are missing or invalid.",
                    },
                    status=400,
                )
        else:
            return JsonResponse({"error": "Request is not authenticated"}, status=401)

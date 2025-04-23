import secrets
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.views import View
from django.views.generic import TemplateView

from dchat_messages.add_hmac import add_hmac
from dchat_messages.models import Connection, DChatFile
from user_profile.models import Profile


class UserProfile(TemplateView):
    template_name = "user_profile/user_profile_config.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context = super().get_context_data(**kwargs)
        user_profile_picture = request.user.profile.profile_picture
        add_hmac(single_object=user_profile_picture)

        context["user"] = request.user

        return super().get(request, *args, **kwargs)


class UpdateProfile(TemplateView):
    template_name = "user_profile/update_profile.html"

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            context = self.get_context_data(**kwargs)
            uploaded_file = request.FILES.get("new_profile_picture", None)
            new_username = request.POST.get("new_username", None)

            if uploaded_file is None and (new_username == "" or new_username is None):
                return JsonResponse(
                    {
                        "error": "Invalid field",
                        "message": "You have to provide values for either or both \
                                of the parameters 'new_profile_picture' and \
                                'new_username'",
                    },
                    status=400,
                )

            user_profile = Profile.objects.get(user=request.user)

            if new_username is not None and new_username != "":
                user_profile.display_name = new_username
                user_profile.save()
                context["display_name_changed"] = True

            if uploaded_file is not None:  # What if user sends a empty file field? TODO
                if "image" in uploaded_file.content_type:
                    file = DChatFile.objects.create(
                        file=uploaded_file,
                        file_name=uploaded_file.name,
                        mime_type=uploaded_file.content_type,
                        token=secrets.token_urlsafe(),
                    )

                    user_profile.profile_picture = file
                    user_profile.save()
                    context["user_profile_changed"] = True
                else:
                    return JsonResponse(
                        {
                            "error": "Invalid field",
                            "message": "File for new profile picture should be a image file.",
                        },
                        status=400,
                    )

            return self.render_to_response(context)

        else:
            return JsonResponse({"error": "Request is not authorized"}, status=401)


channel_layer = get_channel_layer()


def send_new_connection_notification(instance: Connection):
    add_hmac(single_object=instance.user_initiator.profile.profile_picture)
    is_profile_picture = instance.user_initiator.profile.profile_picture
    sender_profile_picture_path = (
        instance.user_initiator.profile.profile_picture.file.url if is_profile_picture else None
    )
    token = instance.user_initiator.profile.profile_picture.token if is_profile_picture else None
    hmac = instance.user_initiator.profile.profile_picture.hmac if is_profile_picture else None
    exp_time = instance.user_initiator.profile.profile_picture.exp_time if is_profile_picture else None
    data = {
        "type": "connection.message",
        "message_type": "new_connection",
        "recipient_type": instance.connection_type.lower(),
        "sender_username": instance.user_initiator.username,
        "sender_profile_picture_path": sender_profile_picture_path,
        "token": token,
        "hmac": hmac,
        "exp_time": exp_time,
    }

    if instance.status == "PENDING":
        async_to_sync(channel_layer.group_send)(
            f"{instance.connection_type.lower()}_{instance.user_acceptor.username}", data
        )


class SendConnectionRequest(TemplateView):
    template_name = "user_profile/send_connection_request.html"

    def post(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            recipient_username = request.POST.get("recipient_username", None)
            if recipient_username is None:
                return JsonResponse({"error": "'recipient_username' field is required."}, status=400)

            recipient_user_qs = get_user_model().objects.filter(username=recipient_username)

            if recipient_user_qs:
                recipient_user = recipient_user_qs.first()
            else:
                return JsonResponse({"error": "The recipient user doesn't exists."}, status=400)

            recipient_has_connection_status = False

            connection_qs = Connection.objects.filter(
                Q(Q(user_initiator=self.request.user, user_acceptor=recipient_user))
                | Q(Q(user_initiator=recipient_user, user_acceptor=self.request.user))
            )

            if connection_qs:
                recipient_has_connection_status = True
                connection = connection_qs.first()

                if connection.status == "PENDING":
                    return JsonResponse({"error": "Request status already in 'PENDING' state."}, status=403)

                # If connection initiator is the requesting user and connection
                # status is in 'BLOCKED' state then that means the recipient
                # user has blocked the connection.
                if connection.user_initiator == self.request.user and connection.status == "BLOCKED":
                    return JsonResponse({"error": "Recipient user has blocked the connection"}, status=403)

                if connection.status == "REJECTED":
                    # Set the initiator and acceptor and change the connection status to 'PENDING'
                    connection.user_initiator = self.request.user
                    connection.user_acceptor = recipient_user
                    connection.connection_type = "USER"
                    connection.status = "PENDING"
                    connection.save()
                    send_new_connection_notification(connection)

                    context["connection"] = connection
                    return self.render_to_response(context=context)

            if recipient_has_connection_status is False:
                # Create new connection
                connection = Connection.objects.create(
                    user_initiator=self.request.user,
                    user_acceptor=recipient_user,
                    connection_type="USER",
                    status="PENDING",
                )

                send_new_connection_notification(connection)
                context["connection"] = connection
                return self.render_to_response(context=context)
        else:
            return JsonResponse({"error": "Request is not authenticated"}, status=403)


class ConnectionRequestResponse(View):
    ...

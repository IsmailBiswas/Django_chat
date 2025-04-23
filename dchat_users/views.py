from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView, never_cache, sensitive_post_parameters
from django.core.exceptions import ValidationError
from django.db.models import Model, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import FormView, HttpResponseRedirect, ImproperlyConfigured

from dchat_messages.add_hmac import add_hmac
from dchat_messages.models import Connection
from dchat_users.models import Verification
from dchat_users.resend_email_verification import ResendEmailVerification

from .forms import CustomUserCreationForm


class ResendEmailVarificationView(TemplateView):
    template_name = "registration/email_not_verified.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        if request.user.is_authenticated:
            verification_obj = Verification.objects.get(user=request.user)
            if not verification_obj.email_verified:
                resend_email = ResendEmailVerification(email=request.user.email, request=request)
                resend_email.send_mail()
                context["email_sent"] = True
        return self.render_to_response(context)


class EmailNotVerified(TemplateView):
    template_name = "registration/email_not_verified.html"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            redirect_url = reverse("homepage")
            return HttpResponseRedirect(redirect_url)
        else:
            verification_obj = Verification.objects.get(user=request.user)
            if verification_obj.email_verified:
                redirect_url = reverse("homepage")
                return HttpResponseRedirect(redirect_url)

        return super().get(request, *args, **kwargs)


class SignUp(FormView):
    template_name = "dchat_users/sign_up.html"
    form_class = CustomUserCreationForm
    success_url = "/accounts/signup"

    def form_valid(self, form):
        form.save(request=self.request)
        messages.success(request=self.request, message="🎉 Account created!")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            verification_obj = Verification.objects.get(user=self.request.user)
            if verification_obj.email_verified:
                redirect_url = reverse("homepage")
                return HttpResponseRedirect(redirect_url)
        return super().get(request, *args, **kwargs)


class LogIn(LoginView):
    template_name = "dchat_users/login.html"


INTERNAL_RESET_SESSION_TOKEN = "_email_verify_token"
UserModel = get_user_model()


class EmailVerify(TemplateView):
    post_reset_login = False
    post_reset_login_backend = None
    reset_url_token = "confirm_email"
    success_url = reverse_lazy("email_verify_complete")
    template_name = "registration/email_verify_confirm.html"
    title = _("Confirm email")
    token_generator = default_token_generator

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured("The URL path must contain 'uidb64' and 'token' parameters.")

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, verify the user.
                    self.validlink = True
                    self.update_verification(self.user)
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # email verification URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, self.reset_url_token)
                    return HttpResponseRedirect(redirect_url)

        # Display the "Email reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context["validlink"] = True
        else:
            context.update(
                {
                    "form": None,
                    "title": _("Email verification unsuccessful"),
                    "validlink": False,
                }
            )
        return context

    def update_verification(self, user):
        verify_obj = Verification.objects.get(user=user)
        verify_obj.email_verified = True
        verify_obj.save()


class Logout(LogoutView):
    next_page = reverse_lazy("log_in")


class NewConnections(ListView):
    """Returns partial html of users list with 'PENDING' connection status"""

    template_name = "dchat_messages/connection_list.html"
    context_object_name = "users"
    model = Connection

    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_type"] = "connection_request"
        return context

    def get_queryset(self):
        query_set = super().get_queryset()
        pending_connections = query_set.filter(
            Q(user_acceptor=self.request.user) & Q(status="PENDING") & Q(group__isnull=True)
        ).select_related("user_initiator", "user_acceptor")

        # Creates a list of tuple the first value in the tuple is the user
        # connected user and second value is the number of unread message for
        # that user
        requesting_users = [
            connection.user_acceptor if connection.user_initiator == self.request.user else connection.user_initiator
            for connection in pending_connections
        ]

        file_objects = [user.profile.profile_picture for user in requesting_users]
        add_hmac(iterable=file_objects)

        return requesting_users


class ConnectionResponse(View):
    """Handles user response to a connection request"""

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)

    def _update_connection(self, sender: Model, new_status: str) -> dict:
        """Updates connection status to provided status, if `sender` is
        user_initiator and acceptor is the user of the request.
        """
        data = {
            "error": True,
            "connection": None,
            "error_object": None,
        }

        connection_qs = Connection.objects.filter(
            user_initiator=sender, user_acceptor=self.request.user, status="PENDING"
        )

        if not connection_qs:
            error_object = JsonResponse({"error": "Provided data is invalid"}, status=400)
            data["error_object"] = error_object
            return data
        else:
            data["error"] = False
            connection = connection_qs.first()
            connection.status = new_status
            connection.save()
            data["connection"] = connection
            return data

    def notify_accepted(self, connection: Connection) -> None:
        channel_layer = get_channel_layer()
        data = {
            "type": "connection.message",
            "message_type": "connection_accepted",
        }

        async_to_sync(channel_layer.group_send)(
            f"{connection.connection_type.lower()}_{connection.user_acceptor.username}", data
        )
        async_to_sync(channel_layer.group_send)(
            f"{connection.connection_type.lower()}_{connection.user_initiator.username}", data
        )

    def post(self, request, *args, **kwargs):
        type_of_action = request.POST.get("action", None)
        sender_username = request.POST.get("sender_username", None)

        if type_of_action is None or sender_username is None:
            return JsonResponse(
                {"error": "Missing required fields", "required_fields": "'sender_username', 'action'"}, status=400
            )

        sender_qs = get_user_model().objects.filter(username=sender_username)
        if not sender_qs:
            return JsonResponse({"error": "Provided username is invalid"}, status=400)
        else:
            sender = sender_qs.first()

        redirect_url = reverse("user_connection", kwargs={"username": sender_username})

        if type_of_action == "accept":
            connection_validity = self._update_connection(sender=sender, new_status="ACCEPTED")
            if connection_validity["error"]:
                return connection_validity["error_object"]
            else:
                connection = connection_validity["connection"]
                self.notify_accepted(connection)
                return redirect(redirect_url)

        elif type_of_action == "reject":
            connection_validity = self._update_connection(sender=sender, new_status="REJECTED")
            if connection_validity["error"]:
                return connection_validity["error_object"]
            else:
                return redirect(redirect_url)

        elif type_of_action == "block":
            connection_validity = self._update_connection(sender=sender, new_status="BLOCKED")
            if connection_validity["error"]:
                return connection_validity["error_object"]
            else:
                return redirect(redirect_url)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)


class BlockedUsers(ListView):
    template_name = "dchat_users/blocked_users.html"
    model = Connection
    context_object_name = "users"

    def get_queryset(self):
        # return super().get_queryset()
        query_set = super().get_queryset()
        accepted_connections = query_set.filter(
            Q(user_acceptor=self.request.user) & Q(status="BLOCKED") & Q(group__isnull=True)
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


class UnblockUser(View):
    def post(self, request, *args, **kwargs):
        blocked_username = request.POST.get("blocked_username", None)
        if blocked_username is None:
            return JsonResponse({"Error": "Blocked user's username not provided"}, status=400)

        blocked_user = get_user_model().objects.filter(username=blocked_username)

        if not blocked_user:
            return JsonResponse({"Error": "Invalid blocked username"}, status=400)
        else:
            blocked_user = blocked_user.first()

        connection = Connection.objects.filter(user_acceptor=request.user, user_initiator=blocked_user)

        if not connection:
            return JsonResponse({"Error": "Invalid connection"}, status=400)
        else:
            connection = connection.first()
            connection.delete()

        return HttpResponse("Unblocked")

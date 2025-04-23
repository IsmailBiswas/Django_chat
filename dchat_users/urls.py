from django.contrib.auth.views import LogoutView
from django.urls import path

from dchat_users.views import (
    BlockedUsers,
    ConnectionResponse,
    EmailNotVerified,
    EmailVerify,
    LogIn,
    NewConnections,
    ResendEmailVarificationView,
    SignUp,
    UnblockUser,
)

# Before url segment is /accounts/
urlpatterns = [
    path("signup/", SignUp.as_view(), name="sign_up"),
    path("login/", LogIn.as_view(), name="log_in"),
    path("emailverify/<uidb64>/<token>/", EmailVerify.as_view(), name="email_verify"),
    path("logout/", LogoutView.as_view(), name="log_out"),
    path("emailnotverified/", EmailNotVerified.as_view(), name="email_not_verified"),
    path("resendemailverification/", ResendEmailVarificationView.as_view(), name="resend_email_verification"),
    path("newconnections/", NewConnections.as_view(), name="new_connections"),
    path("connectionresponse/", ConnectionResponse.as_view(), name="connection_response"),
    path("blockedusers/", BlockedUsers.as_view(), name="blocked_users"),
    path("unblockedusers/", UnblockUser.as_view(), name="unblock_user"),
]

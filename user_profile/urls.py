from django.urls import path

from . import views

urlpatterns = [
    path("user_profile/", views.UserProfile.as_view(), name="user_profile"),
    path("update_profile/", views.UpdateProfile.as_view(), name="update_profile"),
    path("send_connection_request/", views.SendConnectionRequest.as_view(), name="send_connection_request"),
]

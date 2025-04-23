from django.urls import path

from . import views

urlpatterns = [
    path("users/", views.UserList.as_view(), name="connected_users"),
    path("users/<str:username>/", views.UserConnect.as_view(), name="user_connection"),
    path("fileaccess/validate/", views.FileAccessAuth.as_view(), name="file_access_authentication"),
    path("message/", views.ReceiveMessage.as_view(), name="receive_message"),
    path("messagereadack/", views.MessageReadACK.as_view(), name="receive_message_read_acknowledgement"),
]

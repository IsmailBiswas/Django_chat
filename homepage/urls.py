from django.urls import path

from . import views

urlpatterns = [
    path("", views.Homepage.as_view(), name="homepage"),
    path("searchusers/", views.SearchUsers.as_view(), name="search_users"),
]

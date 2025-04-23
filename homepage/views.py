from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.views import HttpResponseRedirect
from django.db.models import Q
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from dchat_messages.add_hmac import add_hmac
from dchat_users.models import Verification


class Homepage(TemplateView):
    template_name = "homepage/homepage.html"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            redirect_url = reverse("log_in")
            return HttpResponseRedirect(redirect_url)

        if self.request.user.is_authenticated:
            verify_obj = Verification.objects.get(user=self.request.user)
            if not verify_obj.email_verified:
                redirect_url = reverse("email_not_verified")
                return HttpResponseRedirect(redirect_url)

        context = super().get_context_data(**kwargs)
        user_profile_picture = request.user.profile.profile_picture
        add_hmac(single_object=user_profile_picture)

        context["user"] = request.user
        return super().get(request, *args, **kwargs)


class SearchUsers(ListView):
    model = get_user_model()
    paginate_by = 20
    template_name = "dchat_messages/connection_list.html"
    context_object_name = "users"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["list_type"] = "user_search"
        context["list-background-color"] = "bg-green-700"
        return context

    def get_queryset(self, *args, **kwargs) -> QuerySet[Any]:
        search_query = self.request.GET.get("search_query", None)
        queryset = get_user_model().objects.filter(
            Q(username__icontains=search_query) | Q(profile__display_name__icontains=search_query)
        )

        file_objects = [user.profile.profile_picture for user in queryset]

        add_hmac(iterable=file_objects)
        return queryset

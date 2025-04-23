import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import RequestFactory

from dchat_users.forms import CustomUserCreationForm
from dchat_users.models import Verification
from dchat_users.views import SignUp


@pytest.mark.django_db
class TestAccountCreation:
    def test_user_creation_works(self):
        data = {
            "password1": "12345test",
            "password2": "12345test",
            "username": "user",
            "email": "user@example.com",
        }
        form = CustomUserCreationForm(data)
        assert form.is_valid()

    def test_username_length_validation(self):
        data = {
            "password1": "12345test",
            "password2": "12345test",
            "username": "ab",  # username less than 4 character long.
            "email": "ab@example.com",
        }
        form = CustomUserCreationForm(data)
        assert not form.is_valid()

    def test_user_creation_creates_verification(self):
        user_model = get_user_model()
        user_info = {
            "username": "user",
            "password": "testpass",
            "email": "user@example.com",
        }
        user = user_model.objects.create(**user_info)

        verification_instance = Verification.objects.filter(user=user).first()
        if verification_instance is not None:
            assert verification_instance.user == user
        else:
            pytest.fail("Verification instance is not getting created.")

    def test_user_creation_sends_email(self):
        factory = RequestFactory()
        url = "/accounts/signup/"
        user = AnonymousUser()
        data = {
            "username": "user1",
            "email": "user1@example.com",
            "password1": "testpass12345",
            "password2": "testpass12345",
        }
        request = factory.post(url, data)
        request.user = user
        SignUp.as_view()(request)
        assert len(mail.outbox) == 1
        # assert mail.outbox[0].body.__contains__(data["username"])

    def _test_if_verification_link_works(self):
        # TODO
        # The EmailVerify view requires sessions, and it also needs to redirect
        # the request to itself after saving the token in sessions. So, I
        # think it would be more effective to conduct this test as an
        # End-to-End test.
        ...

    def _test_login_view(self):
        # TODO
        ...

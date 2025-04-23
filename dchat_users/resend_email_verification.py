from django.contrib.auth.forms import EmailMultiAlternatives, loader
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import get_current_site
from django.utils.crypto import force_bytes
from django.utils.http import urlsafe_base64_encode


class ResendEmailVerification:
    def __init__(self, email, request) -> None:
        self.email = email
        self.request = request

    def execute_send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """

        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=[to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()

    def send_mail(
        self,
        subject_template_name="registration/email_confirm_subject.txt",
        email_template_name="registration/email_confirm.txt",
        html_email_template_name="registration/email_confirm.html",
        from_email=None,
        domain_override=None,
        use_https=False,
        token_generator=default_token_generator,
        extra_email_context=None,
    ):
        if not domain_override:
            current_site = get_current_site(self.request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        context = {
            "email": self.email,
            "domain": domain,
            "site_name": site_name,
            "uid": urlsafe_base64_encode(force_bytes(self.request.user.pk)),
            "user": self.request.user,
            "token": token_generator.make_token(self.request.user),
            "protocol": "https" if use_https else "http",
            **(extra_email_context or {}),
        }

        self.execute_send_mail(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=context,
            from_email=from_email,
            to_email=self.email,
            html_email_template_name=html_email_template_name,
        )

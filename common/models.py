from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    affiliation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    why_account_needed = models.TextField(max_length=1000, blank=True)

    is_approved = models.BooleanField(default=False)
    """This field marks if the user is affiliated with the university or not"""

    note = models.TextField(max_length=1000, blank=True)

    def __str__(self):
        return f"{self.user.email}"


class EmailVerificationTable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)

    def send_verification_email(self):
        html_message = render_to_string(
            "registration/verify_email.html",
            {
                "token": self.token,
            },
        )
        send_mail(
            "Verify your email address on SciLifeLab Serve",
            (
                "You registered an account on SciLifeLab Serve (serve.scilifelab.se).\n"
                "Please click this link to verify your email address:"
                f" https://serve.scilifelab.se/verify/?token={self.token}"
                "\n\n"
                "SciLifeLab Serve team"
            ),
            settings.EMAIL_HOST_USER,
            [self.user.email],
            fail_silently=False,
            html_message=html_message,
        )

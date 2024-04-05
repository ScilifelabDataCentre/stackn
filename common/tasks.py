import time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

from studio.celery import app
from studio.utils import get_logger

logger = get_logger(__name__)

ADMIN_EMAIL = "serve@scilifelab.se"


@app.task
def handle_deleted_users():
    """
    Handles deleted user accounts.

    Using a threshold of 12 months. If the user deleted their account longer ago, then it is handled.
    Initially, user accounts deleted more than 12 months ago will trigger an email to Serve admins
    for manual processing.

    TODO: Make threshold_days a variable in settings.py
    """

    threshold_days = 365
    threshold_time = timezone.now() - timezone.timedelta(days=threshold_days)

    logger.info(f"Running task handle_deleted_users using threshold {threshold_days} days")

    # Get all inactive users
    inactive_users = User.objects.filter(is_active=False)

    for user in inactive_users:
        if user.userprofile.deleted_on is None:
            # This user was not deleted. It is inactive for another reason.
            continue

        if user.userprofile.deleted_on <= threshold_time:
            # The user was deleted over threshold days ago
            # Send an email to Serve admins
            logger.warn(
                f"User {user.id} was deleted over {threshold_days} days ago. Now sending email to Serve admins."
            )

            send_mail(
                "Remove deleted user from SciLifeLab Serve",
                f"The user with id {user.id} deleted their account over {threshold_days} days ago. "
                "Please permanently remove the user from SciLifeLab Serve according to the routines.",
                settings.EMAIL_HOST_USER,
                [ADMIN_EMAIL],
                fail_silently=False,
            )

        else:
            # The user was deleted too recently to be handled. Simply log and exit.
            logger.info(f"User {user.id} was deleted less than {threshold_days} days ago. Exiting.")


@app.task
def alert_pause_inactive_users():
    """
    Handles inactive user accounts.

    Inactive means that the user has not logged into Serve for x months.
    Users inactive for 12 months will trigger an email sent to the user.
    Users inactive for 13 months will be paused (setting user is_active = false)

    TODO: Make these variables in settings.py
    """

    pass

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.models import EmailVerificationTable


@receiver(pre_save, sender=User)
def custom_save(sender, instance, **kwargs):
    """
    This function is used to set the username of the user to the email address.

    We decided to do that in SS-507, because we want to use the email address as the username,
    but we are in the middle of the project live, so django documention points out that
    it is a
    `complicated process to change user model now
    <https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#changing-to-a-custom-user-model-mid-project>`_
    . So we decided to use this signal to set the username to the email address.

    This call back is registered by ``common.apps.CommonConfig.ready()``

    NB! There is also a post save signal that could be found in ``studio.views.py``
    """
    instance.username = instance.email


@receiver(post_save, sender=EmailVerificationTable)
def send_verification_email(sender, instance, created, **kwargs):
    """
    This function is used to send verification email to the user.

    It is registered by ``common.apps.CommonConfig.ready()``
    """
    if created:
        instance.send_verification_email()

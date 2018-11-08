"""
Signal handlers for core app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from wagtail.wagtailusers.models import UserProfile

from journals.apps.core.models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    if created:
        UserProfile.objects.create(
            user=instance,
            submitted_notifications=False,
            approved_notifications=False,
            rejected_notifications=False
        )

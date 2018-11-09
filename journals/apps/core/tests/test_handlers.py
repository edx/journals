"""
Tests for signal handlers
"""
from django.test import TestCase

from journals.apps.core.tests.factories import (
    UserFactory,
)


class TestUserPostSave(TestCase):
    """
    Test Cases for post_save signal of User model.
    """

    def test_notification_settings_disabled_on_user_creation(self):
        """
        Test user's notifications preferences are disabled at the time of user creation
        """
        user = UserFactory()
        self.assertFalse(user.wagtail_userprofile.submitted_notifications)
        self.assertFalse(user.wagtail_userprofile.approved_notifications)
        self.assertFalse(user.wagtail_userprofile.rejected_notifications)

    def test_notification_settings_can_be_enbled(self):
        """
        Test user's notifications preferences can be enabled by updating user's profile
        """
        user = UserFactory()
        userprofile = user.wagtail_userprofile
        userprofile.submitted_notifications = True
        userprofile.approved_notifications = True
        userprofile.rejected_notifications = True
        userprofile.save()
        self.assertTrue(user.wagtail_userprofile.submitted_notifications)
        self.assertTrue(user.wagtail_userprofile.approved_notifications)
        self.assertTrue(user.wagtail_userprofile.rejected_notifications)

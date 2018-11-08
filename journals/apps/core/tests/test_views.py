"""Test core.views."""
from urllib.parse import urljoin

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from rest_framework import status
from wagtail.wagtailcore.models import Site

from journals.apps.core.constants import Status
from journals.apps.core.tests.factories import UserFactory, SiteConfigurationFactory

User = get_user_model()


class HealthTests(TestCase):
    """Tests of the health endpoint."""

    def test_all_services_available(self):
        """Test that the endpoint reports when all services are healthy."""
        self._assert_health(200, Status.OK, Status.OK)

    # TODO: WL-1713: this test is failing because the SiteMiddleware throws a 500 error before the health method runs
    #   so this test is commented out until WL-1713 is addressed
    # def test_database_outage(self):
    #     """Test that the endpoint reports when the database is unavailable."""
    #     with mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.cursor', side_effect=DatabaseError):
    #         self._assert_health(503, Status.UNAVAILABLE, Status.UNAVAILABLE)

    def _assert_health(self, status_code, overall_status, database_status):
        """Verify that the response matches expectations."""
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response['content-type'], 'application/json')

        expected_data = {
            'overall_status': overall_status,
            'detailed_status': {
                'database_status': database_status
            }
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)


class AutoAuthTests(TestCase):
    """ Auto Auth view tests. """
    AUTO_AUTH_PATH = reverse('auto_auth')

    @override_settings(ENABLE_AUTO_AUTH=False)
    def test_setting_disabled(self):
        """When the ENABLE_AUTO_AUTH setting is False, the view should raise a 404."""
        response = self.client.get(self.AUTO_AUTH_PATH)
        self.assertEqual(response.status_code, 404)

    @override_settings(ENABLE_AUTO_AUTH=True)
    def test_setting_enabled(self):
        """
        When ENABLE_AUTO_AUTH is set to True, the view should create and authenticate
        a new User with superuser permissions.
        """
        original_user_count = User.objects.count()
        response = self.client.get(self.AUTO_AUTH_PATH)

        # Verify that a redirect has occured and that a new user has been created
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), original_user_count + 1)

        # Get the latest user
        user = User.objects.latest()

        # Verify that the user is logged in and that their username has the expected prefix
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(user.username.startswith(settings.AUTO_AUTH_USERNAME_PREFIX))

        # Verify that the user has superuser permissions
        self.assertTrue(user.is_superuser)


@ddt.ddt
class TestUserRequireAuthView(TestCase):
    """
    Test Cases for required_auth
    """

    def setUp(self):
        super(TestUserRequireAuthView, self).setUp()

        self.user = UserFactory()
        self.site = Site.objects.first()
        self.site_configuration = SiteConfigurationFactory(site=self.site)
        self.client.login(username=self.user.username, password='password')
        self.path = reverse("require_auth")

    @ddt.data(
        ("http://evil.com", False, status.HTTP_403_FORBIDDEN),
        ("/cms/", False, status.HTTP_302_FOUND),
        ("/cms/", True, status.HTTP_302_FOUND),
    )
    @ddt.unpack
    def test_unauthorized_calls(self, url, join_base_url, expected_status):
        if join_base_url:
            base_url = RequestFactory().get('/').build_absolute_uri()
            url = urljoin(base_url, url)
        response = self.client.get(self.path, {"forward": url})
        self.assertEqual(response.status_code, expected_status)

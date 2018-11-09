""" Test Cases for middleware """
import ddt
from mock import PropertyMock, patch

from django.conf import settings
from django.test import TestCase
from wagtail.wagtailcore.models import Site

from journals.apps.core.tests.factories import (
    SiteConfigurationFactory,
    SiteFactory
)


@ddt.ddt
class TestSettingsMiddleware(TestCase):
    """
    Test Cases for middleware.
    """

    @ddt.data(
        ('example.com', 'no-reply@example.com'),
        ('dummy.org', 'notification@test.com'),
        ('test.co.name', 'no-reply@test.co.name'),
    )
    @ddt.unpack
    def test_notification_settings_override(self, hostname, from_email):
        """
        Test WAGTAILADMIN_NOTIFICATION_FROM_EMAIL setting override based on site
        """
        site = SiteFactory(hostname=hostname)
        site_configuration = SiteConfigurationFactory(site=site, from_email=from_email)
        url = "http://{}".format(site.hostname)
        with patch.object(Site, 'find_for_request') as requested_site:
            requested_site.return_value = site
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(settings.WAGTAILADMIN_NOTIFICATION_FROM_EMAIL, site_configuration.from_email)

    @ddt.data(
        ('http', 'example.com'),
        ('https', 'dummy.org'),
        ('ftp', 'test.co.name'),
    )
    @ddt.unpack
    @patch('django.core.handlers.wsgi.WSGIRequest.get_host')
    @patch('django.core.handlers.wsgi.WSGIRequest.scheme', new_callable=PropertyMock)
    def test_base_url_setting_override(self, scheme, hostname, mock_scheme, mock_host):
        """
        Test BASE_URL setting override
        """
        url = "{}://{}".format(scheme, hostname)
        mock_scheme.return_value = scheme
        mock_host.return_value = hostname
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(settings.BASE_URL, url)

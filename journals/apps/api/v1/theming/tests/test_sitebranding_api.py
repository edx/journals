""" Tests for /api/v1/sitebranding/ API """
import json

from django.test import TestCase

from journals.apps.core.tests.factories import (USER_PASSWORD,
                                                SiteBrandingFactory,
                                                SiteConfigurationFactory,
                                                SiteFactory, UserFactory)


class TestSiteBrandingAPI(TestCase):
    """ Test Cases for /api/v1/sitebranding/ API """

    def setUp(self):
        super(TestSiteBrandingAPI, self).setUp()

        self.user = UserFactory()

        self.path = "/api/v1/sitebranding/"
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    def _create_site_branding_configurations(self):
        """ Create SiteFactory and associated SiteBrandingFactory and SiteConfigurationFactory """
        site = SiteFactory()
        site_branding = SiteBrandingFactory(site=site)
        site_configuration = SiteConfigurationFactory(site=site)

        return {
            'frontend_url': site_configuration.frontend_url,
            'theme_name': site_branding.theme_name,
            'site_logo': {
                'title': site_branding.site_logo.title,
                'file': site_branding.site_logo.file,
            }
        }

    def _assert_site_branding_equal(self, response, test_site_branding):
        """ Assert that the response site branding is equal to the test data """
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(response_json), 1, "Only 1 item should be returned")
        self.assertEqual(response_json[0]['theme_name'], test_site_branding['theme_name'])
        self.assertEqual(response_json[0]['site_logo']['title'], test_site_branding['site_logo']['title'])
        self.assertIn(test_site_branding['site_logo']['file'].name, response_json[0]['site_logo']['file'])

    def test_get_sitebranding_query_param_frontend_url(self):
        """ Test that sitebranding API returns the site branding when the 'frontend_url' query param is set """
        # create test data
        test_site_1 = self._create_site_branding_configurations()
        test_site_2 = self._create_site_branding_configurations()

        # get test site 1
        response = self.client.get(self.path, {'frontend_url': test_site_1['frontend_url']})
        self._assert_site_branding_equal(response, test_site_1)

        # get test site 2
        response = self.client.get(self.path, {'frontend_url': test_site_2['frontend_url']})
        self._assert_site_branding_equal(response, test_site_2)

    def test_no_site_configuration_for_frontend_url(self):
        """ Test that if the frontend_url is not associated with any site configuration we get [] back """
        # create test data
        self._create_site_branding_configurations()

        # request with a fake front end url
        response = self.client.get(self.path, {'frontend_url': 'fake-url'})
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertFalse(response_json, "Response JSON should be empty")

    def test_no_site_branding_for_site_configuration(self):
        """ Test that if there is no site branding associated with the site configuration """
        # create site config and associated site, but do not create an associated site branding
        site_configuration = SiteConfigurationFactory()

        # request the site branding associated with that site configuration
        response = self.client.get(self.path, {'frontend_url': site_configuration.frontend_url})
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertFalse(response_json, "Response JSON should be empty")

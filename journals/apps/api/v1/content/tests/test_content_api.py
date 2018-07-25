""" Test Cases for /api/v1/content/ APIs """
import datetime
import json

from django.test import TestCase
from django.urls import reverse

from journals.apps.core.tests.factories import (
    JournalFactory,
    JournalAccessFactory,
    OrganizationFactory,
    SiteFactory,
    UserFactory,
    USER_PASSWORD
)
from journals.apps.core.tests.utils import (
    TEST_JOURNAL_STRUCTURE,
    create_journal_about_page_factory,
    is_nested_json_equivalent
)


class TestContentPagesAPI(TestCase):
    """ Test Cases for /api/v1/content/pages/ API """

    def setUp(self):
        super(TestContentPagesAPI, self).setUp()

        self.user = UserFactory()
        self.test_about_page_slug = 'journal-about-page-slug'
        self.site = SiteFactory()
        self.org = OrganizationFactory(site=self.site)
        self.journal = JournalFactory(
            organization=self.org
        )
        self.journal_access = JournalAccessFactory(
            journal=self.journal,
            user=self.user,
            expiration_date=datetime.date.today() + datetime.timedelta(days=1)
        )
        self.journal_about_page = create_journal_about_page_factory(
            journal=self.journal,
            journal_structure=self.journal_test_data,
            about_page_slug=self.test_about_page_slug
        )
        self.path = reverse('content:pages:listing')
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    @property
    def journal_test_data(self):
        return TEST_JOURNAL_STRUCTURE

    def test_get_pages(self):

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['total_count'], 11, "Incorrect number of pages")

    def test_query_pages_by_slug(self):
        """ Test that the correct page is returned when using 'slug' query param """
        # Test slug for about page
        response = self.client.get(self.path, {'slug': self.test_about_page_slug})
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['total_count'], 1, "Should only get one page")

        page_json = response_json['items'][0]
        self.assertEqual(page_json['title'], self.journal_test_data['title'])
        self.assertEqual(page_json['meta']['type'], 'journals.JournalAboutPage')

        # Test slug for one of the journal pages
        # Journal pages slugs should be the same as their titles if there are no spaces
        test_page_data = self.journal_test_data['structure'][0]
        response = self.client.get(self.path, {'slug': test_page_data['title']})
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['total_count'], 1, "Should only get one page")

        page_json = response_json['items'][0]
        self.assertEqual(page_json['title'], test_page_data['title'])
        self.assertEqual(page_json['meta']['type'], 'journals.JournalPage')

    def test_get_journal_about_page_with_structure(self):
        """ Get journal about page and check that it returns the correct structure """
        response = self.client.get(self.path, {
            'slug': self.test_about_page_slug,
            'type': 'journals.JournalAboutPage',
            'fields': 'structure'
        })

        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['total_count'], 1, "Should only get one page")

        page_json = response_json['items'][0]
        self.assertTrue(is_nested_json_equivalent(page_json, self.journal_test_data))

""" Test Cases for Journal Page """

from django.test import TestCase
from django.urls import reverse

from journals.apps.core.tests.factories import (
    UserFactory,
    OrganizationFactory,
    JournalFactory,
    SiteConfigurationFactory,
    SiteFactory,
    USER_PASSWORD
)
from journals.apps.journals.models import JournalPage
from journals.apps.core.tests.utils import (
    create_journal_about_page_factory,
)
from journals.apps.journals.handlers import (
    connect_page_signals_handlers,
    disconnect_page_signals_handlers,
)


class TestJournalPage(TestCase):
    """
    Test Cases for Journal Page.
    """

    def setUp(self):
        super(TestJournalPage, self).setUp()
        self.user = UserFactory()
        self.user.is_superuser = True
        self.user.save()
        self.site = SiteFactory()
        self.site_configuration = SiteConfigurationFactory(site=self.site)
        self.org = OrganizationFactory(site=self.site)
        self.journal = JournalFactory(
            organization=self.org
        )
        self.journal_about_page = create_journal_about_page_factory(
            journal=self.journal,
            journal_structure=self.journal_test_data,
            about_page_slug='journal-about-page-slug'
        )
        self.path = reverse('wagtailadmin_explore_root')
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    @property
    def journal_test_data(self):
        """
        Returns the test data\
        """
        return {
            "title": "test_journal_about_page",
            "structure": [
                {
                    "title": "test_page_1",
                    "children": [
                        {
                            "title": "test_page_1_child_1",
                            "children": [
                                {
                                    "title": "test_page_1_grand_child_1",
                                    "children": [
                                        {
                                            "title": "test_page_1_grand_child_1_grand_child_1",
                                            "children": [
                                                {
                                                    "title": "test_page_1_grand_child_1_grand_child_1_grand_child_1",
                                                    "children": []
                                                },
                                            ]
                                        },
                                        {
                                            "title": "test_page_1_grand_child_1_grand_child_2",
                                            "children": []
                                        }
                                    ]
                                },
                                {
                                    "title": "test_page_1_grand_child_2",
                                    "children": []
                                }
                            ]
                        }
                    ]
                },
            ]
        }

    @classmethod
    def setUpClass(cls):
        super(TestJournalPage, cls).setUpClass()
        disconnect_page_signals_handlers()

    @classmethod
    def tearDownClass(cls):
        connect_page_signals_handlers()
        super(TestJournalPage, cls).tearDownClass()

    def _get_previous_page(self, page):
        """
        Returns the previous page of journals page
        """
        return JournalPage.objects.get(title=page.title).get_prev_page()

    def _get_next_page(self, page):
        """
        Returns the next page of journals page
        """
        return JournalPage.objects.get(title=page.title).get_next_page()

    def test_pub_unpub_pub_pattern(self):
        """
        Test the 'pub->unpub->pub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        self.journal_about_page.save_revision().publish()
        self.journal_about_page.get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].save_revision().publish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_child_pages[0]))  # because its unpublished

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_child_pages[0]).title,
            "test_page_1_child_1"
        )

    def test_unpub_unpub_pub_pattern(self):
        """
        Test the 'unpub->unpub->pub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].save_revision().publish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_child_pages[0]))  # because its unpublished

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_child_pages[0]).title,
            "test_page_1_child_1"
        )

    def test_unpub_pub_pub_pattern(self):
        """
        Test the 'unpup->pub->pub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[0].save_revision().publish()
        self.journal_about_page.get_children()[0].get_children()[0].save_revision().publish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_child_pages[0]).title,
            "test_page_1"
        )

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_child_pages[0]).title,
            "test_page_1_child_1"
        )

    def test_pub_unpub_unpub_pub_pattern(self):
        """
        Test the 'pub->unpub->unpub->pub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.save_revision().publish()
        self.journal_about_page.get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].get_children()[0].save_revision().publish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_child_pages[0]))

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_grand_child_pages[0]))

        journal_grand_grand_child_pages = journal_grand_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_grand_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )

    def test_unpub_pub_unpub_pub_pattern(self):
        """
        Test the 'unpub->pub->unpub->pub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[0].save_revision().publish()
        self.journal_about_page.get_children()[0].get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].get_children()[0].save_revision().publish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_child_pages[0]).title,
            "test_page_1"
        )

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_child_pages[0]).title,
            "test_page_1"
        )

        journal_grand_grand_child_pages = journal_grand_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_grand_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )

    def test_unpub_pattern(self):
        """
        Test the 'unpub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.unpublish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_child_pages[0]).title,
            "test_page_1"
        )

    def test_pub_unpub_pattern(self):
        """
        Test the 'pub->unpub' pattern
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.journal_about_page.unpublish()

        journal_pages = self.journal_about_page.get_children()
        self.assertEqual(
            self._get_next_page(journal_pages[0]).title,
            "test_page_1_child_1"
        )
        self.assertIsNone(self._get_previous_page(journal_pages[0]))  # because its journal_about_page

        journal_child_pages = journal_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_child_pages[0]).title,
            "test_page_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_child_pages[0]).title,
            "test_page_1"
        )

        journal_grand_child_pages = journal_child_pages[0].get_children()
        self.assertEqual(
            self._get_next_page(journal_grand_child_pages[0]).title,
            "test_page_1_grand_child_1_grand_child_1"
        )
        self.assertEqual(
            self._get_previous_page(journal_grand_child_pages[0]).title,
            "test_page_1_child_1"
        )

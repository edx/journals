"""
Test Cases for journal about page
"""
from django.test import TestCase
from django.urls import reverse

from journals.apps.core.tests.factories import (
    JournalFactory,
    OrganizationFactory,
    SiteFactory,
    SiteConfigurationFactory,
    UserFactory,
    USER_PASSWORD,
)
from journals.apps.core.tests.utils import (
    create_journal_about_page_factory,
)
from journals.apps.journals.handlers import (
    connect_page_signals_handlers,
    disconnect_page_signals_handlers,
)


class TestJournalAboutPageStructure(TestCase):
    """ Test Cases for journal about page structure """

    @classmethod
    def setUpClass(cls):
        super(TestJournalAboutPageStructure, cls).setUpClass()
        disconnect_page_signals_handlers()

    @classmethod
    def tearDownClass(cls):
        connect_page_signals_handlers()
        super(TestJournalAboutPageStructure, cls).tearDownClass()

    def setUp(self):
        super(TestJournalAboutPageStructure, self).setUp()

        self.user = UserFactory()
        self.user.is_superuser = True
        self.user.save()
        self.test_about_page_slug = 'journal-about-page-slug'
        self.site = SiteFactory()
        self.site_configuration = SiteConfigurationFactory(site=self.site)
        self.org = OrganizationFactory(site=self.site)
        self.journal = JournalFactory(
            organization=self.org
        )
        self.journal_about_page = create_journal_about_page_factory(
            journal=self.journal,
            journal_structure=self.journal_test_data,
            about_page_slug=self.test_about_page_slug
        )

        self.path = reverse('wagtailadmin_explore_root')
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    @property
    def journal_test_data(self):
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
                                    "children": []
                                },
                                {
                                    "title": "test_page_1_grand_child_2",
                                    "children": []
                                }
                            ]
                        },
                        {
                            "title": "test_page_1_child_2",
                            "children": []
                        }
                    ]
                },
                {
                    "title": "test_page_2",
                    "children": []
                },
                {
                    "title": "test_page_3",
                    "children": [
                        {
                            "title": "test_page_3_child_1",
                            "children": []
                        },
                        {
                            "title": "test_page_3_child_2",
                            "children": []
                        }
                    ]
                }
            ]
        }

    def _assert_page_hierarchy(self):
        """
        asserts pages under journal about page are in correct hierarchy
        """
        # assert journal about page has right child count
        self.assertEqual(self.journal_about_page.get_descendant_count(), 9)
        self.assertEqual(self.journal_about_page.get_children_count(), 3)
        journal_pages = self.journal_about_page.get_children()
        for index, page in enumerate(journal_pages):
            self.assertEqual(page.title, "_".join(["test_page", str(index + 1)]))

        # assert journal pages has right child count
        journal_page_1 = journal_pages[0]
        self.assertEqual(journal_page_1.get_children_count(), 2)
        journal_page_1_children = journal_page_1.get_children()
        for index, page in enumerate(journal_page_1_children):
            self.assertEqual(page.title, "_".join(["test_page_1_child", str(index + 1)]))

        journal_page_2 = journal_pages[1]
        self.assertEqual(journal_page_2.get_children_count(), 0)

        journal_page_3 = journal_pages[2]
        self.assertEqual(journal_page_3.get_children_count(), 2)
        journal_page_3_children = journal_page_3.get_children()
        for index, page in enumerate(journal_page_3_children):
            self.assertEqual(page.title, "_".join(["test_page_3_child", str(index + 1)]))

        # assert journal page has right grand child count
        journal_page_1_child_1_children = journal_page_1_children[0].get_children()
        self.assertEqual(len(journal_page_1_child_1_children), 2)
        for index, page in enumerate(journal_page_1_child_1_children):
            self.assertEqual(page.title, "_".join(["test_page_1_grand_child", str(index + 1)]))

        self.assertEqual(journal_page_1_children[1].get_children_count(), 0)

    def test_get_pages(self):
        """
        Tests journal about page structure under different publish/unpublish scenarios
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        self.journal_about_page.save_revision().publish()
        self.journal_about_page.get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].save_revision().publish()
        self._assert_page_hierarchy()

        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[2].unpublish()
        self.journal_about_page.get_children()[2].get_children()[1].save_revision().publish()
        self._assert_page_hierarchy()

        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[2].save_revision().publish()
        self.journal_about_page.get_children()[2].get_children()[1].save_revision().publish()
        self._assert_page_hierarchy()

        self.journal_about_page.save_revision().publish()
        self.journal_about_page.get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].get_children()[0].save_revision().publish()
        self._assert_page_hierarchy()

        self.journal_about_page.unpublish()
        self.journal_about_page.get_children()[0].save_revision().publish()
        self.journal_about_page.get_children()[0].get_children()[0].unpublish()
        self.journal_about_page.get_children()[0].get_children()[0].get_children()[0].save_revision().publish()
        self._assert_page_hierarchy()

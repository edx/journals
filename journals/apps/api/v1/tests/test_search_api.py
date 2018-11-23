""" Test Cases for /api/v1/search/ APIs """
import datetime
import json
import uuid

from django.core import management
from django.db.models import Q
from django.template.defaultfilters import striptags
from django.test import TestCase
from django.urls import reverse
from wagtail.wagtailcore.models import Site

from journals.apps.api.v1.search.views import TYPE_ALL, PARAM_TYPE, PARAM_QUERY, PARAM_OPERATOR, OPERATOR_AND, \
    OPERATOR_OR, TYPE_IMAGE, TYPE_DOCUMENT, TYPE_VIDEO
from journals.apps.core.tests.factories import (
    JournalFactory,
    JournalAccessFactory,
    OrganizationFactory,
    UserFactory,
    USER_PASSWORD, RAW_HTML_BLOCK_DATA)
from journals.apps.core.tests.utils import (
    TEST_JOURNAL_STRUCTURE, create_journal_about_page_factory)
from journals.apps.journals.blocks import RICH_TEXT_BLOCK_TYPE
from journals.apps.journals.models import JournalImage, JournalDocument, Video, JournalPage


class TestSearchAPI(TestCase):
    """ Test Cases for /api/v1/search API """

    @classmethod
    def setUpClass(cls):
        super(TestSearchAPI, cls).setUpClass()

        cls.test_about_page_slug = 'journal-about-page-slug'

        cls.user = UserFactory()
        cls.site = Site.objects.first()
        cls.org = OrganizationFactory(site=cls.site)
        cls.journal = JournalFactory(
            organization=cls.org
        )
        cls.journal_access = JournalAccessFactory(
            journal=cls.journal,
            user=cls.user,
            expiration_date=datetime.date.today() + datetime.timedelta(days=1)
        )
        cls.journal_about_page = create_journal_about_page_factory(
            journal=cls.journal,
            journal_structure=cls.get_journal_test_data(),
            root_page=cls.site.root_page,
            about_page_slug=cls.test_about_page_slug,
        )

        cls._update_index()

        cls.multi_journal_search_path = reverse('api:v1:multi_journal_search')
        cls.single_journal_search_path = reverse('api:v1:journal_search', args=(cls.journal.id,))
        cls.common_query_string = 'title'

    def setUp(self):
        super(TestSearchAPI, self).setUp()
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    @staticmethod
    def _update_index():
        management.call_command('update_index')

    @staticmethod
    def get_journal_test_data():
        return TEST_JOURNAL_STRUCTURE

    def _make_assertions(self, response, doc_count, image_count, video_count, total):
        """ Makes response assertions for search response """
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['doc_count'], doc_count, "Incorrect number of docs")
        self.assertEqual(response_json['meta']['image_count'], image_count, "Incorrect number of images")
        self.assertEqual(response_json['meta']['video_count'], video_count, "Incorrect number of videos")
        self.assertEqual(response_json['meta']['total_count'], total, "Incorrect total results")

    def _search_across_multiple_journals(self, query_string):
        """ search querystring across multi journals and make assertions"""
        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: query_string,
            PARAM_TYPE: TYPE_ALL
        })
        self.assertEqual(response.status_code, 200)
        doc_count = JournalDocument.objects.filter(title__icontains=query_string).count()
        image_count = JournalImage.objects.filter(title__icontains=query_string).count()
        video_count = Video.objects.filter(display_name__icontains=query_string).count()
        total = doc_count + image_count + video_count

        self._make_assertions(response, doc_count, image_count, video_count, total)

    def _search_single_journal(self, query_string):
        """
            Search single journal that is self.journal
        """
        response = self.client.get(self.single_journal_search_path, {PARAM_QUERY: query_string, PARAM_TYPE: TYPE_ALL})

        self.assertEqual(response.status_code, 200)
        journal_filter_kwargs = {
            'journalpage__journal_about_page__journal': self.journal,
        }
        doc_count = JournalDocument.objects.filter(title__icontains=query_string, **journal_filter_kwargs).count()
        image_count = JournalImage.objects.filter(title__icontains=query_string, **journal_filter_kwargs).count()
        video_count = Video.objects.filter(display_name__icontains=query_string, **journal_filter_kwargs).count()
        total = doc_count + image_count + video_count

        self._make_assertions(response, doc_count, image_count, video_count, total)

    def test_search_across_multiple_journals(self):
        """ test search multiple journals"""
        query_strings = ('title', 'doc', 'video', 'image')
        for query in query_strings:
            self._search_across_multiple_journals(query)

    def test_search_single_journal(self):
        """ test search singe journal"""

        # create some more JournalPages, DOCs, Images and Videos with some random journal
        create_journal_about_page_factory(
            journal=JournalFactory(organization=self.org, uuid=uuid.uuid4()),
            journal_structure=self.get_journal_test_data(),
            root_page=self.site.root_page,
            about_page_slug='journal-about-page-slug-1',
        )
        self._update_index()
        # import pdb; pdb.set_trace()
        query_strings = ('title', 'doc', 'video', 'image')
        for query in query_strings:
            self._search_single_journal(query)

    def test_search_across_multi_journals_without_permission(self):
        # create some more JournalPages, DOCs, Images and Videos with some random journal without JournalAccess
        create_journal_about_page_factory(
            journal=JournalFactory(organization=self.org, uuid=uuid.uuid4()),
            journal_structure=self.get_journal_test_data(),
            root_page=self.site.root_page,
            about_page_slug='journal-about-page-slug-1',
        )
        self._update_index()

        query_string = self.common_query_string
        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: query_string,
            PARAM_TYPE: TYPE_ALL
        })
        self.assertEqual(response.status_code, 200)

        # user have only access to self.journal, so search should only contain related results
        filter_kwargs = {
            'journalpage__journal_about_page__journal': self.journal,
        }
        doc_count = JournalDocument.objects.filter(title__icontains=query_string, **filter_kwargs).count()
        image_count = JournalImage.objects.filter(title__icontains=query_string, **filter_kwargs).count()
        video_count = Video.objects.filter(display_name__icontains=query_string, **filter_kwargs).count()
        total = doc_count + image_count + video_count

        self._make_assertions(response, doc_count, image_count, video_count, total)

    def test_search_across_multiple_journals_with_OR_operator(self):
        """
            Testing search with OR operator
        """
        query_string = 'title+doc'

        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: query_string,
            PARAM_OPERATOR: OPERATOR_OR,
            PARAM_TYPE: TYPE_ALL
        })
        self.assertEqual(response.status_code, 200)
        doc_count = JournalDocument.objects.filter(Q(title__icontains='title') | Q(title__icontains='doc')).count()
        image_count = JournalImage.objects.filter(Q(title__icontains='title') | Q(title__icontains='doc')).count()
        video_count = Video.objects.filter(
                Q(display_name__icontains='title') | Q(display_name__icontains='doc')
            ).count()
        total = doc_count + image_count + video_count

        self._make_assertions(response, doc_count, image_count, video_count, total)

    def test_search_across_multiple_journals_with_AND_operator(self):
        """
            Testing search with AND operator (Note: AND has been overridden to 'phrase' type)
        """
        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: RAW_HTML_BLOCK_DATA,
            PARAM_OPERATOR: OPERATOR_AND,
            PARAM_TYPE: TYPE_ALL
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))

        # as each page contains same raw_html i.e RAW_HTML_BLOCK_DATA, so we expect same page count is search results
        page_count = JournalPage.objects.count()
        # because non of these have RAW_HTML_BLOCK_DATA in there content/title
        doc_count = video_count = image_count = 0
        total = page_count + video_count + image_count + doc_count

        # make assertions
        self.assertEqual(response_json['meta']['text_count'], page_count, "Incorrect number of text_count")
        self._make_assertions(response, doc_count, image_count, video_count, total)

    def test_search_across_multiple_journals_with_DOC_type(self):
        """
            Testing Document type search

            common query string is substring of all types(i.e video, images and doc etc)
            but we should get search results for Doc type
        """

        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: self.common_query_string,
            PARAM_OPERATOR: OPERATOR_OR,
            PARAM_TYPE: TYPE_DOCUMENT
        })
        self.assertEqual(response.status_code, 200)

        doc_count = JournalDocument.objects.filter(title__icontains=self.common_query_string).count()
        self._make_assertions(response, doc_count=doc_count, image_count=0, video_count=0, total=doc_count)

    def test_search_across_multiple_journals_with_IMAGE_types(self):
        """
            Testing Image type search

            common query string is substring of all types(i.e video, images and doc etc)
            but we should get search results for Image type
        """

        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: self.common_query_string,
            PARAM_TYPE: TYPE_IMAGE
        })
        image_count = JournalImage.objects.filter(title__icontains=self.common_query_string).count()
        self.assertEqual(response.status_code, 200)
        self._make_assertions(response, doc_count=0, image_count=image_count, video_count=0, total=image_count)

    def test_search_across_multiple_journals_with_VIDEO_types(self):
        """
            Testing Video type search

            common query string is substring of all types(i.e video, images and doc etc)
            but we should get search results for Video type
        """

        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: self.common_query_string,
            PARAM_OPERATOR: OPERATOR_OR,
            PARAM_TYPE: TYPE_VIDEO
        })
        self.assertEqual(response.status_code, 200)
        video_count = Video.objects.filter(display_name__icontains=self.common_query_string).count()
        self._make_assertions(response, doc_count=0, image_count=0, video_count=video_count, total=video_count)

    def test_raw_html(self):
        """ search querystring across multi journals and make assertions"""
        response = self.client.get(self.multi_journal_search_path, {
            PARAM_QUERY: RAW_HTML_BLOCK_DATA,
            PARAM_TYPE: TYPE_ALL
        })

        # as each page contains same raw_html, so we expect same is search results
        page_count = JournalPage.objects.count()

        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_json['meta']['text_count'], page_count, "Incorrect number of text_count")
        for hit in response_json['hits']:
            if hit['block_type'] == RICH_TEXT_BLOCK_TYPE:
                self.assertIn(RAW_HTML_BLOCK_DATA, striptags(hit['highlights'][0]))

    def test_search_multiple_journals_with_no_query_params(self):
        response = self.client.get(self.multi_journal_search_path)
        self.assertEqual(response.status_code, 200)
        self._make_assertions(response, 0, 0, 0, 0)

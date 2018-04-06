'''Journal Models'''
from __future__ import absolute_import, unicode_literals

import base64
import datetime
import json
import logging
import requests
import uuid

from django.db import models
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from edx_rest_api_client.client import EdxRestApiClient

from model_utils.models import TimeStampedModel

from journals.apps.core.models import User
from journals.apps.search.backend import LARGE_TEXT_FIELD_SEARCH_PROPS

from jsonfield.fields import JSONField

from urllib.parse import urlsplit, urlunsplit

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtaildocs.models import AbstractDocument, Document
from wagtail.wagtailimages.models import Image
from wagtail.wagtailsearch import index


logger = logging.getLogger(__name__)


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    site = models.ForeignKey(
        'wagtailcore.Site',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Journal(models.Model):
    """
    A collection of informational articles to which access can be purchased.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    video_course_ids = JSONField(
        verbose_name=_('Video Source Course IDs'),
        help_text=_('List of course IDs to pull videos from'),
        null=False,
        blank=False,
        default={'course_runs': []}
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        null=True
    )
    access_length = models.DurationField()

    def __str__(self):
        return self.name


class JournalAccess(TimeStampedModel):
    """
    Represents a learner's access to a journal.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User)
    journal = models.ForeignKey(Journal)
    expiration_date = models.DateField()

    def __str__(self):
        return str(self.uuid)

    @classmethod
    def user_has_access(cls, user, journal):
        """ Checks if the user has access to this journal """
        if user.is_staff:
            return True

        access_items = cls.objects.filter(
            user=user
        ).filter(
            journal=journal
        ).filter(
            expiration_date__lte=datetime.date.today()
        )
        return True if access_items else False

    @classmethod
    def create_journal_access(cls, user, journal):
        """ Creates new journal access for user """
        expiration_date = datetime.datetime.now() + journal.access_length

        access = cls.objects.create(
            user=user,
            journal=journal,
            expiration_date=expiration_date,
        )
        access.save()
        return access


class JournalDocument(AbstractDocument):
    '''
    Override the base Document model so we can index the Document contents for search
    and add reference to JournalAboutPage
    '''
    search_fields = AbstractDocument.search_fields + [
        index.SearchField('data', partial_match=False),
        index.FilterField('id')
    ]

    admin_form_fields = Document.admin_form_fields

    def data(self):
        '''
        Return the contents of the document as base64 encoded
        data used as input to elasticsearch ingest-attachment plugin
        '''
        self.file.open()
        contents = base64.b64encode(self.file.read()).decode('ascii')
        self.file.close()
        print('in get data for file=', self.file.name)
        return contents


class Video(index.Indexed, models.Model):
    '''
    Video model
    '''
    block_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=255)
    view_url = models.URLField(max_length=255)
    transcript_url = models.URLField(max_length=255)
    source_course_run = models.CharField(max_length=255)

    search_fields = [
        index.SearchField('display_name', partial_match=True),
        index.SearchField('transcript', partial_match=False, es_extra=LARGE_TEXT_FIELD_SEARCH_PROPS),
        index.FilterField('id')
    ]

    def transcript(self):
        '''
        Read the transcript from the transcript url to provide
        to elasticsearch
        '''
        try:
            response = requests.get(self.transcript_url) # No auth needed for transcripts
            contents = response.content
            return contents.decode('utf-8') if contents else None
        except Exception as err:
            print('Exception trying to read transcript', err)
            return None

    def __str__(self):
        return self.display_name

# This has to be below the Video model because XBlockVideoBlock imported below imports the Video model.
from .blocks import (
    JournalRichTextBlock, JournalImageChooserBlock, PDFBlock, XBlockVideoBlock,
    PDF_BLOCK_TYPE, VIDEO_BLOCK_TYPE, IMAGE_BLOCK_TYPE, RICH_TEXT_BLOCK_TYPE,
    STREAM_DATA_DOC_FIELD, STREAM_DATA_TYPE_FIELD)


class JournalAboutPage(Page):
    """
    Represents both the base journal with it's metadata and the journal
    marketing page that displays that information.
    """
    journal = models.OneToOneField(Journal, on_delete=models.SET_NULL, null=True, blank=True)
    # title = journal.title ???
    card_image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.SET_NULL, related_name='+', null=True
    )
    hero_image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.SET_NULL, related_name='+', null=True
    )
    short_description = models.CharField(max_length=128, blank=True, default='')
    long_description = models.TextField(blank=True, default=None, null=True)
    custom_content = RichTextField(blank=True)


    content_panels = Page.content_panels + [
        FieldPanel('short_description'),
        FieldPanel('long_description'),
        ImageChooserPanel('card_image'),
        ImageChooserPanel('hero_image'),
        FieldPanel('custom_content'),
    ]

    parent_page_types = ['JournalIndexPage']
    subpage_types = ['JournalPage']

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published pages
        context = super(JournalAboutPage, self).get_context(request, args, kwargs)
        context['root_journal_page_url'] = self.root_journal_page_url
        if request.user.is_authenticated():
            context['user_has_access'] = JournalAccess.user_has_access(request.user, self.journal)
        else:
            context['user_has_access'] = False
        discovery_journal_api_client = self.site.siteconfiguration.discovery_journal_api_client
        journal_data = discovery_journal_api_client.journals(self.journal.uuid).get()
        context['journal_data'] = journal_data
        context['buy_button_url'] = self.generate_basket_url(journal_data['sku'])
        return context

    def generate_basket_url(self, sku):
        ecommerce_base_url = self.site.siteconfiguration.ecommerce_public_url_root
        (scheme, netloc, _, _, _) = urlsplit(ecommerce_base_url)
        basket_url = urlunsplit((
            scheme,
            netloc,
            '/basket/add/',
            f'sku={sku}',
            ''
        ))
        return basket_url

    @property
    def site(self):
        return self.journal.organization.site

    @property
    def root_journal_page_url(self):
        descendants = self.get_descendants()
        return descendants[0].full_url if descendants else '#'


class JournalIndexPage(Page):
    """
    The marketing page that shows all the journals available on a given site.
    Publicly available.
    """
    subpage_types = ['JournalAboutPage']

    hero_image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.SET_NULL, related_name='+', null=True
    )
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        ImageChooserPanel('hero_image'),
        FieldPanel('intro', classname="full"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro', partial_match=True),
        index.SearchField('search_description', partial_match=True)
    ]

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published pages
        context = super(JournalIndexPage, self).get_context(request, args, kwargs)
        context['journalaboutpage'] = self.get_children().live()
        return context


class JournalPage(Page):
    """
    A page inside a journal. These can be nested indefinitely. Restricted to
    users who purchased access to the journal.
    """
    parent_page_types = ['JournalAboutPage', 'JournalPage']
    subpage_types = ['JournalPage']

    body = StreamField([
        (RICH_TEXT_BLOCK_TYPE, JournalRichTextBlock(
            features=['h1', 'h2', 'h3', 'ol', 'ul', 'bold', 'italic', 'link', 'hr', 'document-link', 'image']
        )),
        (IMAGE_BLOCK_TYPE, JournalImageChooserBlock()),
        (PDF_BLOCK_TYPE, PDFBlock()),
        (VIDEO_BLOCK_TYPE, XBlockVideoBlock()),
    ], blank=True)

    videos = models.ManyToManyField(Video)
    documents = models.ManyToManyField(JournalDocument)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body')
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body', partial_match=True),
        index.SearchField('search_description', partial_match=True)
    ]

    def update_related_objects(self, clear=False):
        '''
        Update the relationship of related objects (docs, videos)
        This gets called when page is published/unpublished
        '''
        if not clear:
            new_docs, new_videos, new_images = self._get_related_objects(documents=True, videos=True, images=False)
        else:
            new_docs = set()
            new_videos = set()

        self.documents.set(new_docs)
        self.videos.set(new_videos)

    def _get_related_objects(self, documents=True, videos=True, images=True):
        '''
        Find set of related objects found in page
        Returns:
        document set(), video set(), image set()
        each containg a list of corresponding objects models
        '''
        doc_set = set()
        video_set = set()
        image_set = set()

        for data in self.body.stream_data:
            # TODO: search for images/docs embedded in RichText block as well
            block_type = data.get(STREAM_DATA_TYPE_FIELD, None)
            if documents and block_type == PDF_BLOCK_TYPE:
                doc_set.add(JournalDocument.objects.get(id=data.get('value').get(STREAM_DATA_DOC_FIELD)))
            elif videos and block_type == VIDEO_BLOCK_TYPE:
                video_set.add(Video.objects.get(id=data.get('value').get('video')))
            elif images and block_type == IMAGE_BLOCK_TYPE:
                image_set.add(Image.objects.get(id=data.get('value')))

        return doc_set, video_set, image_set

    def get_context(self, request, *args, **kwargs):
        context = super(JournalPage, self).get_context(request, args, kwargs)
        context['journal_structure'] = self.get_journal_structure()

        # context['prevPage'] = self.get_prev_page()
        # context['nextPage'] = self.get_next_page()

        return context

    def get_prev_page(self):
        '''
        Get the previous page for navigation. Search order is previous sibling's last descendant,
        previous sibling, then parent
        '''
        prev_sib = self.get_prev_sibling()
        if prev_sib:
            last_child = prev_sib.specific.get_last_descendant()
            return last_child if last_child else prev_sib

        parent = self.get_parent()
        return parent if parent and not parent.is_root() else None

    def get_next_page(self, children_and_sibs=True):
        '''
        Get the next page for navigation. Search order is child, sibling then
        parent next sibling recursively
        '''
        if children_and_sibs:
            next_child = self.get_first_child()
            next_sib = self.get_next_sibling()

            if next_child or next_sib:
                return next_child or next_sib

        # no direct children or siblings, now lets recursively check parent's siblings
        parent = self.get_parent()
        if parent.is_root():
            return None
        next_sib = parent.get_next_sibling()
        return next_sib if next_sib else parent.specific.get_next_page(children_and_sibs=False)

    def get_last_descendant(self):
        '''
        get the last descendant of this page
        '''
        children = self.get_descendants()
        return children[len(children) - 1] if children else None

    def serve(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login/')
        journal = self.get_parent_journal()
        has_access = JournalAccess.user_has_access(request.user, journal)
        if not has_access:
            raise PermissionDenied
        return super(JournalPage, self).serve(request, args, kwargs)

    def get_parent_journal(self):
        """ Moves up tree of pages until it finds an about page and returns it's linked journal """
        journal_about = self.get_journal_about_page()
        return journal_about.journal

    def get_journal_about_page(self):
        journal_about = None
        parent = self.get_parent()
        journal_about = parent.specific
        while True:
            if isinstance(parent.specific, JournalAboutPage):
                journal_about = parent.specific
                break
            try:
                parent = parent.get_parent()
            except:
                logging.error("Cannot find parent of {}".format(self))
                break
        return journal_about

    def get_journal_structure(self):
        """ Returns the heirarchy of the journal as a dict """
        journal_about_page = self.get_journal_about_page()
        structure = {
            "journal_structure": [
                journal_page.specific.get_nested_children()
                for journal_page
                in journal_about_page.get_children()
            ]
        }
        return structure

    def get_json_journal_structure(self):
        return json.dumps(self.get_journal_structure())


    def get_nested_children(self):
        structure = {
            "title": self.title,
            "url": self.url,
            "children": None
        }
        children = self.get_children()
        if not children:
            return structure

        structure["children"] = [child.specific.get_nested_children() for child in children]
        return structure

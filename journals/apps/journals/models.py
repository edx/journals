from __future__ import absolute_import, unicode_literals

from django.db import models
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from model_utils.models import TimeStampedModel

from journals.apps.core.models import User
from journals.apps.search.backend import LARGE_TEXT_FIELD_SEARCH_PROPS
from journals.apps.journals.api_client.lms import JwtLmsApiClient

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtaildocs.models import AbstractDocument, Document
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailimages.models import Image
from wagtail.wagtailsearch import index

import base64
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class Journal(models.Model):
    """
    A collection of informational articles to which access can be purchased.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

class JournalAccess(TimeStampedModel):
    """
    Represents a learner's access to a journal. 
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User)
    journal = models.ForeignKey(Journal)

    def __str__(self):
        return str(self.uuid)

    @classmethod
    def user_has_access(cls, user, journal):
        """ Checks if the user has access to this journal """
        access_items = cls.objects.filter(user=user).filter(journal=journal)
        return True if access_items else False


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
        # return the contents of the document, base64 encoded
        # data used as input to elasticsearch ingest-attachment plugin
        self.file.open()
        contents = base64.b64encode(self.file.read()).decode('ascii')
        self.file.close()
        print('in get data for file=', self.file.name)
        return contents

class Video(index.Indexed, models.Model):
    block_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=512)
    view_url = models.URLField(max_length=512)
    transcript_url = models.URLField(max_length=512)

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
            contents = JwtLmsApiClient().get_video_transcript(self.transcript_url)
            return contents.decode('utf-8') if contents else None
        except Exception as err:
            print('Exception trying to read transcript', err)
            return None

    def __str__(self):
        return self.display_name

# This has to be below the Video model because XBlockVideoBlock imported below imports the Video model.
from .blocks import (
    JournalRichTextBlock, JournalRawHTMLBlock, JournalImageChooserBlock, PDFBlock, TOCBlock, XBlockVideoBlock,
    PDF_BLOCK_TYPE, VIDEO_BLOCK_TYPE, IMAGE_BLOCK_TYPE, RICH_TEXT_BLOCK_TYPE, RAW_HTML_BLOCK_TYPE,
    TOC_BLOCK_TYPE, STREAM_DATA_DOC_FIELD, STREAM_DATA_TYPE_FIELD)

class JournalAboutPage(Page):
    """
    Represents both the base journal with it's metadata and the journal
    marketing page that displays that information.
    """
    journal = models.OneToOneField(Journal, on_delete=models.SET_NULL, null=True, blank=True)

    parent_page_types = ['JournalIndexPage']
    subpage_types = ['JournalPage']


class JournalIndexPage(Page):
    """
    The marketing page that shows all the journals available on a given site.
    Publicly available.
    """
    subpage_types = ['JournalAboutPage']
    
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro', partial_match=True),
        index.SearchField('search_description', partial_match=True)
    ]

    def get_context(self, request):
        # Update context to include only published pages
        context = super(JournalIndexPage, self).get_context(request)
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
        (RICH_TEXT_BLOCK_TYPE, JournalRichTextBlock(features=['h1', 'h2', 'h3', 'ol', 'ul', 'bold', 'italic', 'link', 'hr', 'document-link', 'image'])),
        (RAW_HTML_BLOCK_TYPE, JournalRawHTMLBlock()),
        (IMAGE_BLOCK_TYPE, JournalImageChooserBlock()),
        (PDF_BLOCK_TYPE, PDFBlock()),
        (TOC_BLOCK_TYPE, TOCBlock()),
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
            type = data.get(STREAM_DATA_TYPE_FIELD, None)
            if documents and type == PDF_BLOCK_TYPE:
                doc_set.add(JournalDocument.objects.get(id=data.get('value').get(STREAM_DATA_DOC_FIELD)))
            elif videos and type == VIDEO_BLOCK_TYPE:
                video_set.add(Video.objects.get(id=data.get('value').get('video')))
            elif images and type == IMAGE_BLOCK_TYPE:
                image_set.add(Image.objects.get(id=data.get('value')))

        return doc_set, video_set, image_set

    def get_context(self, request):
        context = super(JournalPage, self).get_context(request)

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


    def serve(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login/')
        journal = self.get_parent_journal()
        has_access = JournalAccess.user_has_access(request.user, journal)
        if not has_access:
            raise PermissionDenied
        return super(JournalPage, self).serve(request)

    def get_parent_journal(self):
        """ Moves up tree of pages until it finds an about page and returns it's linked journal """
        journal_about = None
        parent = self.get_parent()
        journal_about = parent.specific
        while True:
            if isinstance(parent.specific, JournalAboutPage):
                journal_about = parent.specific
                break
            try:
                parent = self.get_parent()
            except:
                logging.error("Cannot find parent of {}".format(self))
        return journal_about.journal
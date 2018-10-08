"""
Module to define background tasks for search related features
"""
import logging

from background_task import background
from wagtail.wagtailsearch.backends import get_search_backends

log = logging.getLogger(__name__)


@background(schedule=30)
def task_index_journal_document(document_id):
    """
    Task to create elastic search index for journal documents
    """
    from journals.apps.journals.models import JournalDocument
    from journals.apps.search.backend import INGEST_ATTACHMENT_ID

    try:
        item = JournalDocument.objects.get(pk=document_id)
    except JournalDocument.DoesNotExist:
        log.error('JournalDocument with id %s does not exist', document_id)
        return

    for backend in get_search_backends():
        search_index = backend.get_index_for_model(type(item))
    mapping = search_index.mapping_class(item.__class__)
    results = search_index.es.index(
        search_index.name,
        mapping.get_document_type(),
        mapping.get_document(item),
        pipeline=INGEST_ATTACHMENT_ID,
        id=mapping.get_document_id(item)
    )
    log.info('indexed document with attachment results=%s', results)


@background(schedule=30)
def task_index_journal_video(video_id):
    """
    Task to create elastic search index for videos
    """
    from journals.apps.journals.models import Video

    try:
        item = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        log.error('Video with id %s does not exist', video_id)
        return

    for backend in get_search_backends():
        search_index = backend.get_index_for_model(type(item))

    # call add_item method of base class to avoid recursive loop
    super(search_index.__class__, search_index).add_item(item)
    log.info('indexed video with id=%s', video_id)

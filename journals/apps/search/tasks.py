"""
Module to define celery tasks for search related features
"""
import logging

from celery.task import task
from wagtail.wagtailsearch.backends import get_search_backends

log = logging.getLogger(__name__)


@task(bind=True, default_retry_delay=10, max_retries=2)
def task_index_journal_document(self, document_id):  # pylint: disable=unused-argument
    """
    Celery task to create elastic search index for journal documents
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


@task(bind=True, default_retry_delay=10, max_retries=2)
def task_index_journal_video(self, video_id):  # pylint: disable=unused-argument
    """
    Celery task to create elastic search index for videos
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

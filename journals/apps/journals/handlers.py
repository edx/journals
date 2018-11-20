"""
Handlers for journal page signals
"""
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from journals.apps.journals.utils import delete_block_references
from wagtail.wagtailcore.signals import page_published, page_unpublished

from .models import JournalAboutPage, JournalPage, JournalDocument, JournalImage


def page_pub_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    journal_page = kwargs['instance']
    journal_page.update_related_objects()


def page_unpub_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    journal_page = kwargs['instance']
    journal_page.update_related_objects(clear=True)


def about_page_pub_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    journal_about_page = kwargs['instance']
    journal_about_page.update_related_objects()


def about_page_unpub_receiver(sender, **kwargs):  # pylint: disable=unused-argument
    journal_about_page = kwargs['instance']
    journal_about_page.update_related_objects(deactivate=True)


def connect_page_signals_handlers():
    page_published.connect(page_pub_receiver, sender=JournalPage)
    page_unpublished.connect(page_unpub_receiver, sender=JournalPage)
    page_published.connect(about_page_pub_receiver, sender=JournalAboutPage)
    page_unpublished.connect(about_page_unpub_receiver, sender=JournalAboutPage)


def disconnect_page_signals_handlers():
    page_published.disconnect(page_pub_receiver, sender=JournalPage)
    page_unpublished.disconnect(page_unpub_receiver, sender=JournalPage)
    page_published.disconnect(about_page_pub_receiver, sender=JournalAboutPage)
    page_unpublished.disconnect(about_page_unpub_receiver, sender=JournalAboutPage)


@receiver(pre_delete, sender=JournalDocument)
def delete_document_references(sender, instance, *args, **kwargs):      # pylint: disable=unused-argument
    """
    Pre_delete signal for JournalDocument which deletes the
    document's references from the related journal pages.
    """
    from .blocks import PDF_BLOCK_TYPE
    delete_block_references(instance, PDF_BLOCK_TYPE)


@receiver(pre_delete, sender=JournalImage)
def delete_image_references(sender, instance, *args, **kwargs):     # pylint: disable=unused-argument
    """
    Pre_delete signal for JournalImage which deletes the
    image's references from the related journal pages.
    """
    from .blocks import IMAGE_BLOCK_TYPE
    delete_block_references(instance, IMAGE_BLOCK_TYPE)


connect_page_signals_handlers()

"""
Handlers for journal page signals
"""
from wagtail.wagtailcore.signals import page_published, page_unpublished
from .models import JournalAboutPage, JournalPage


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


page_published.connect(page_pub_receiver, sender=JournalPage)
page_unpublished.connect(page_unpub_receiver, sender=JournalPage)
page_published.connect(about_page_pub_receiver, sender=JournalAboutPage)
page_unpublished.connect(about_page_unpub_receiver, sender=JournalAboutPage)

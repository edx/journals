from wagtail.wagtailcore.signals import page_published, page_unpublished
from .models import JournalPage


def pub_receiver(sender, **kwargs):
    journal_page = kwargs['instance']
    journal_page.update_related_objects()


def unpub_receiver(sender, **kwargs):
    journal_page = kwargs['instance']
    journal_page.update_related_objects(clear=True)

page_published.connect(pub_receiver, sender=JournalPage)
page_unpublished.connect(unpub_receiver, sender=JournalPage)

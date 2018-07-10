"""
Wagtail hooks to customize wagtail operations for journals
"""
from wagtail.wagtailadmin.site_summary import PagesSummaryItem
from wagtail.wagtailcore import hooks
from wagtail.wagtaildocs.wagtail_hooks import DocumentsSummaryItem
from wagtail.wagtaildocs.permissions import permission_policy as document_permission_policy
from wagtail.wagtailimages.wagtail_hooks import ImagesSummaryItem
from wagtail.wagtailimages.permissions import permission_policy as image_permission_policy

from journals.apps.journals.models import WagtailModelManager


class JournalsPagesSummaryItem(PagesSummaryItem):
    """
    Class to customize page summary count
    """

    def get_context(self):
        context = super(JournalsPagesSummaryItem, self).get_context()
        context['total_pages'] = WagtailModelManager.get_user_pages(self.request.user).count()
        return context


class JournalsImagesSummaryItem(ImagesSummaryItem):
    """
    Class to customize image summary count
    """

    def get_context(self):
        context = super(JournalsImagesSummaryItem, self).get_context()
        context['total_images'] = WagtailModelManager.get_user_images(self.request.user).count()
        return context


class JournalsDocumentsSummaryItem(DocumentsSummaryItem):
    """
    Class to customize document summary count
    """

    def get_context(self):
        context = super(JournalsDocumentsSummaryItem, self).get_context()
        context['total_docs'] = WagtailModelManager.get_user_documents(self.request.user).count()
        return context


@hooks.register('construct_explorer_page_queryset')
def pages_user_has_permissions(parent_page, pages, request):  # pylint: disable=unused-argument
    """
    Returns onl those pages where user has editable permissions
    """
    if request.user.is_superuser:
        return pages

    return WagtailModelManager.get_user_pages(request.user, pages=pages)


@hooks.register('construct_homepage_summary_items')
def add_pages_summary_item(request, items):
    """
    Replaces summary items with customize summary items having user's permission base stats.
    """
    if request.user.is_superuser:
        return

    del items[:]
    items.append(JournalsPagesSummaryItem(request))
    items.append(JournalsImagesSummaryItem(request))
    items.append(JournalsDocumentsSummaryItem(request))


@hooks.register('construct_document_chooser_queryset')
def documents_with_add_or_change_permissions_only(documents, request):  # pylint: disable=unused-argument
    """
    Show documents from those collections where user has add or change permissions
    """

    return document_permission_policy.instances_user_has_any_permission_for(
        request.user, ['add', 'change']
    )


@hooks.register('construct_image_chooser_queryset')
def images_with_add_or_change_permissions_only(images, request):  # pylint: disable=unused-argument
    """
    Show images from those collections where user has add or change permissions
    """

    return image_permission_policy.instances_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
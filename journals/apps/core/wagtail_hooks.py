"""
Wagtail hooks to customize wagtail operations for journals
"""

from django.conf.urls import url
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin.rich_text import HalloPlugin
from wagtail.wagtailadmin.site_summary import PagesSummaryItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.whitelist import allow_without_attributes
from wagtail.wagtaildocs.permissions import permission_policy as document_permission_policy
from wagtail.wagtaildocs.wagtail_hooks import DocumentsSummaryItem
from wagtail.wagtailimages.permissions import permission_policy as image_permission_policy
from wagtail.wagtailimages.wagtail_hooks import ImagesSummaryItem

from journals.apps.journals.models import WagtailModelManager
from journals.apps.journals.wagtailadmin.forms import GroupVideoPermissionFormSet
from journals.apps.journals.wagtailadmin.views import AdminCommandsView


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


class CommandsMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_staff


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


@hooks.register('insert_editor_css')
def editor_css():
    return """
    <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.13.1/styles/default.min.css">
    """


@hooks.register('insert_editor_js')
def editor_js():
    """
    Method to insert video relate JS snippet in page editor
    """
    js_files = [
        static('js/video/chooser/video-chooser.js'),
        '//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.13.1/highlight.min.js',
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}"></script>',
        ((filename, ) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.videoChooser = '{0}';
            window.chooserUrls.insertCodeBlock = '{1}';
            registerHalloPlugin('hallowagtailcodeblock');
            hljs.configure({{languages: ['javascript', 'xml', 'python']}});
            hljs.initHighlightingOnLoad();
        </script>
        """,
        urlresolvers.reverse('journals:video_chooser'),
        urlresolvers.reverse('journals:insert_code_block'),
    )


@hooks.register('construct_whitelister_element_rules')
def whitelist_element_rules():
    return {
        'pre': allow_without_attributes,
        'code': allow_without_attributes,
    }


@hooks.register('register_rich_text_features')
def register_embed_feature(features):
    """
    Hook to register custom richtext features
    """
    features.register_editor_plugin(
        'hallo', 'code-block',
        HalloPlugin(
            name='hallowagtailcodeblock',
            js=['js/lib/halo_codeblock_plugin.js'],
        )
    )
    features.default_features.append('code-block')


@hooks.register('register_group_permission_panel')
def register_video_permissions_panel():
    return GroupVideoPermissionFormSet


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^commands/$', AdminCommandsView.as_view(), name='run-admin-commands'),
    ]


@hooks.register('register_settings_menu_item')
def register_run_commands_menu_item():
    return CommandsMenuItem(
        _('Run Commands'),
        urlresolvers.reverse('run-admin-commands'),
        classnames='icon icon-cogs',
        order=1000
    )


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/journals_editor.css'))

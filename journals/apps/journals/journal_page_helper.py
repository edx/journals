""" Helpers for Journal Page Types """
import uuid
from urllib.parse import urljoin

from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers
from django.template.defaultfilters import pluralize
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.models import PagePermissionTester, UserPagePermissionsProxy
from journals.apps.journals.utils import get_cache_key


class JournalPagePermissionTester(PagePermissionTester):
    def can_delete(self):
        """
            Overridden to prevent some pages from being deleted from CMS
        """
        from journals.apps.journals.models import JournalIndexPage, JournalAboutPage
        if isinstance(self.page.specific, (JournalAboutPage, JournalIndexPage)):
            return False
        return super(JournalPagePermissionTester, self).can_delete()


class UserJournalPagePermissionsProxy(UserPagePermissionsProxy):
    def for_page(self, page):
        """Return a PagePermissionTester object that can be used to query whether this user has
        permission to perform specific tasks on the given page"""
        return JournalPagePermissionTester(self, page)


class JournalPageMixin(object):
    """ This class contains methods that are shared between Journal Page Types """

    def flatten_children(self, children):
        """
        Children should always be a list of dicts. In the case that a there is an unpublished page between two
        published pages, the unpublished page will simply be a list of it's children, instead of a dict of it's
        content, plus a children field. This flattens that list of children into the parent list children to keep
        a valid tree structure.
        """
        flat_children = []
        for child in children:
            if isinstance(child, dict):
                flat_children.append(child)
            elif isinstance(child, list):
                for subchild in child:
                    flat_children.append(subchild)
        return flat_children

    def get_nested_children(self, live_only=True):
        """ Return dict hierarchy with self as root """

        # TODO: can remove "url" field once we move to seperated front end
        if self.live:
            structure = {
                "title": self.title,
                "children": None,
                "id": self.id,
                "url": self.url
            }
        else:
            structure = None

        children = self.get_children()
        if not children or (live_only and self.get_descendants().live().count() == 0):
            return structure

        if structure:
            structure_children = [
                struct for struct in
                (
                    child.specific.get_nested_children(live_only=live_only)
                    for child in children
                )
                if struct is not None
            ]
            structure["children"] = self.flatten_children(structure_children)
        else:
            structure = [
                struct for struct in
                (
                    child.specific.get_nested_children(live_only=live_only)
                    for child in children
                )
                if struct is not None
            ]
            structure = self.flatten_children(structure)

        return structure

    def get_serializer(self, request):
        """
        Get the serializer for the given Page object using the same
        mechanism used by the wagtail api.
        Inspired by:
        https://stackoverflow.com/questions/42539670/wagtail-serializing-page-model
        """

        # import here to avoid circular dependency
        from journals.apps.api.v1.views import ManualPageSerializerViewSet
        from journals.apps.api.v1.content.urls import wagtail_router
        from journals.apps.api.v1.content.views import JournalPagesAPIEndpoint

        # This is manual setup of the serializer class
        # args:
        #   wagtail_router: the router to use for wagtail api
        #   type: the type of Page (i.e. journals.JournalPage)
        #   field_config: '*' means serialize all fields defined in base PageSerializer class plus all APIFields,
        #                  others args in the tuple are ignored
        serializer_class = JournalPagesAPIEndpoint._get_serializer_class(  # pylint: disable=protected-access
            wagtail_router,
            type(self),
            [('*', False, None)]
        )

        serializer = serializer_class(
            self, context={'request': request, 'view': ManualPageSerializerViewSet(), 'router': wagtail_router})

        return serializer

    def serve(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Override serve to redirect to frontend app
        This gets called whenever a page is requested to be viewed live
        from the Wagtail admin
        """
        response = redirect(
            urljoin(
                request.site.siteconfiguration.frontend_url,
                self.get_frontend_page_path()
            )
        )

        add_never_cache_headers(response)
        return response

    def serve_preview(self, request, mode_name):  # pylint: disable=unused-argument
        """
        This method gets called from Wagtail when a page is previewed.
        We override to cache the page and redirect to the Journals Frontend App,
        which fetches page from cache (via REST call) and displays the page.
        """
        if not request.user.is_authenticated():
            return redirect('/login/')

        # if page_ptr_id not set means the preview is for a new page that
        # hasn't been created/saved yet
        if not self.page_ptr_id:
            self.page_ptr_id = 0
            self.id = 0

        cache_key = get_cache_key(
            uuid=str(uuid.uuid4()),
            page_id=int(self.page_ptr_id)
        )

        page_data = self.get_serializer(request).data

        cache.set(cache_key, page_data, 300)  # cache for 5 minutes

        response = redirect(
            urljoin(
                request.site.siteconfiguration.frontend_url,
                '{preview_path}/{key}'.format(
                    preview_path=self.get_frontend_preview_path(),
                    key=cache_key
                )
            )
        )
        add_never_cache_headers(response)
        return response

    def permissions_for_user(self, user):
        """
        Return a PagePermissionsTester object defining what actions the user can perform on this page
        """
        user_perms = UserJournalPagePermissionsProxy(user)
        return user_perms.for_page(self)


class ReferencedObjectMixin(object):
    """
    Mixin class that has helper methods for objects referenced by Journal Pages
    """
    def is_image(self):
        return self.get_object_type() == "image"

    def is_document(self):
        return self.get_object_type() == "document"

    def get_journal_page_usage(self):
        """
        Returns image's usage in journal pages.
        """
        from journals.apps.journals.models import JournalPage
        if self.is_image():
            return JournalPage.objects.filter(images=self)
        elif self.is_document():
            return JournalPage.objects.filter(documents=self)
        return None

    @property
    def deletion_warning_message(self):
        """
        Returns the custom deletion warning message
        if image is being used in journal pages.
        """
        object_type = self.get_object_type()

        warning_message = _(  # pylint: disable=no-member
            "Are you sure you want to delete this {object}?"
        ).format(object=object_type)
        journal_pages_title = self.get_journal_page_usage().values_list('title', flat=True)
        if journal_pages_title:
            warning_message = _(  # pylint: disable=no-member
                "The {object} <b>{title}</b> is being used in page{plural}: <b>{page_titles}</b>."
                "<p>Deleting it will remove the {object} from the page{plural} as well."
                "<p>Are you sure you want to delete the {object}?"
            ).format(
                object=object_type,
                title=self.title,
                plural=pluralize(len(journal_pages_title)),
                page_titles=', '.join(journal_pages_title)
            )
        return warning_message

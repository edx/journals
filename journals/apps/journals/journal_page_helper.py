""" Helpers for Journal Page Types """
import uuid
from urllib.parse import urljoin
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers

from journals.apps.journals.utils import get_cache_key

from wagtail.api.v2.endpoints import PagesAPIEndpoint

FRONTEND_PREVIEW_PATH = 'preview'


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

        # This is manual setup of the serializer class
        # args:
        #   wagtail_router: the router to use for wagtail api
        #   type: the type of Page (i.e. journals.JournalPage)
        #   field_config: '*' means serialize all fields defined in base PageSerializer class plus all APIFields,
        #                  others args in the tuple are ignored
        serializer_class = PagesAPIEndpoint._get_serializer_class(  # pylint: disable=protected-access
            wagtail_router,
            type(self),
            [('*', False, None)]
        )

        serializer = serializer_class(
            self, context={'request': request, 'view': ManualPageSerializerViewSet(), 'router': wagtail_router})

        return serializer

    def serve(self, request, *args, **kwargs):
        """
        Override serve to redirect to frontend app
        This gets called whenever a page is requested to be viewed live
        from the Wagtail admin
        """
        if not settings.FRONTEND_ENABLED:
            return super(JournalPageMixin, self).serve(request, args, kwargs)

        response = redirect(
            urljoin(
                request.site.siteconfiguration.frontend_url,
                self.get_frontend_page_path()
            )
        )

        add_never_cache_headers(response)
        return response

    def serve_preview(self, request, mode_name):
        """
        This method gets called from Wagtail when a page is previewed.
        We override to cache the page and redirect to the Journals Frontend App,
        which fetches page from cache (via REST call) and displays the page.
        """
        if not settings.FRONTEND_ENABLED:
            return super(JournalPageMixin, self).serve_preview(request, mode_name)

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
                    preview_path=FRONTEND_PREVIEW_PATH,
                    key=cache_key
                )
            )
        )
        add_never_cache_headers(response)
        return response

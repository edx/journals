""" Helpers for Journal Page Types """
import uuid
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers

from journals.apps.journals.utils import get_cache_key

from wagtail.api.v2.endpoints import PagesAPIEndpoint

FRONTEND_PREVIEW_PATH = '/preview'


class JournalPageMixin(object):
    """ This class contains methods that are shared between Journal Page Types """

    def get_nested_children(self):
        """ Return dict hierarchy with self as root """

        # TODO: can remove "url" field once we move to seperated front end
        structure = {
            "title": self.title,
            "children": None,
            "id": self.id,
            "url": self.url
        }
        children = self.get_children()
        if not children:
            return structure

        structure["children"] = [child.specific.get_nested_children() for child in children]
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

        cache_key = get_cache_key(
            uuid=str(uuid.uuid4()),
            page_id=int(self.id)
        )

        page_data = self.get_serializer(request).data

        cache.set(cache_key, page_data, 300)  # cache for 5 minutes

        # Get site associated with current journal page
        site = self.site if self.site else request.site
        frontend_url = site.siteconfiguration.frontend_url

        response = redirect(
            '{frontend_url}{preview_path}/{key}'.format(
                frontend_url=frontend_url,
                preview_path=FRONTEND_PREVIEW_PATH,
                key=cache_key
            )
        )
        add_never_cache_headers(response)
        return response
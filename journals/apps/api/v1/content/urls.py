"""
Wagtail APIs
"""
from wagtail.api.v2.router import WagtailAPIRouter

from journals.apps.api.v1.content.views import JournalPagesAPIEndpoint

wagtail_router = WagtailAPIRouter('content')

wagtail_router.register_endpoint('pages', JournalPagesAPIEndpoint)

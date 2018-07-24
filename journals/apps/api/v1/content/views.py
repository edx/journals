"""
Overridden Wagtail API endpoints
"""
from rest_framework.permissions import AllowAny
from wagtail.api.v2.endpoints import PagesAPIEndpoint

from journals.apps.api.filters import PageAuthorizationFilter


class JournalPagesAPIEndpoint(PagesAPIEndpoint):
    """
    Filters out some page types if the requesting user doesn't have access to them.

    We need to return JournalIndexPage and JournalAboutPage content types to everyone (including anonymous).
    We also need to check a user's access to a Journal before returning any JournalPage attached to that journal.
    """

    permission_classes = (AllowAny, )
    filter_backends = [PageAuthorizationFilter] + PagesAPIEndpoint.filter_backends

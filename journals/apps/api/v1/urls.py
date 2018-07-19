""" API v1 URLs. """
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from journals.apps.api.v1.preview.views import get_page_preview
from journals.apps.api.v1.theming.views import SiteBrandingViewSet
from journals.apps.api.v1.search.views import SearchViewSet
from journals.apps.api.v1.views import CurrentUserView, JournalAccessViewSet, UserPageVisitView


router = DefaultRouter()
router.register(r'journalaccess', JournalAccessViewSet, base_name='journalaccess')
router.register(r'sitebranding', SiteBrandingViewSet, base_name='sitebranding')

urlpatterns = router.urls

urlpatterns += [
    url(
        r'^users/(?P<user_id>[\d]+)/pagevisits',
        UserPageVisitView.as_view(),
        name="userpagevisit"
    ),
    url(
        r'^preview/(?P<cache_key>.+)/$',
        get_page_preview
    ),
    url(
        r'^users/current',
        CurrentUserView.as_view(),
        name="currentuser"
    ),
    url(
        r'^search/$',
        SearchViewSet.as_view(),
        name='multi_journal_search'
    ),
    url(
        r'^search/(?P<journal_id>[\d]+)/$',
        SearchViewSet.as_view(),
        name='journal_search'
    ),
]

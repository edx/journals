""" API v1 URLs. """
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from journals.apps.api.v1.preview.views import PreviewView
from journals.apps.api.v1.theming.views import SiteBrandingViewSet, SiteInformationView
from journals.apps.api.v1.search.views import SearchView
from journals.apps.api.v1.views import CurrentUserView, JournalAccessViewSet, UserPageVisitViewSet, UserAccountView


router = DefaultRouter()
router.register(r'journalaccess', JournalAccessViewSet, base_name='journalaccess')
router.register(r'sitebranding', SiteBrandingViewSet, base_name='sitebranding')
router.register(r'userpagevisits', UserPageVisitViewSet, base_name='userpagevisit')

urlpatterns = router.urls

urlpatterns += [
    url(
        r'^preview/(?P<cache_key>.+)/$',
        PreviewView.as_view(),
        name="preview"
    ),
    url(
        r'^users/current',
        CurrentUserView.as_view(),
        name="currentuser"
    ),
    url(
        r'^search/$',
        SearchView.as_view(),
        name='multi_journal_search'
    ),
    url(
        r'^search/(?P<journal_id>[\d]+)/$',
        SearchView.as_view(),
        name='journal_search'
    ),
    url(
        r'^siteinfo/$',
        SiteInformationView.as_view(),
        name="siteinfo"
    ),
    url(
        r'^useraccount/$',
        UserAccountView.as_view(),
        name="useraccount"
    ),
]

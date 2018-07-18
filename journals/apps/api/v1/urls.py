""" API v1 URLs. """
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from journals.apps.api.v1.preview.views import get_page_preview
from journals.apps.api.v1.theming.views import SiteBrandingViewSet
from journals.apps.api.v1.views import JournalAccessViewSet, UserPageVisitView


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
]

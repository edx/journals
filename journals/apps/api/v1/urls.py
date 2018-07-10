""" API v1 URLs. """
from rest_framework.routers import DefaultRouter

from journals.apps.api.v1.theming.views import SiteBrandingViewSet
from .views import JournalAccessViewSet

router = DefaultRouter()
router.register(r'journalaccess', JournalAccessViewSet, base_name='journalaccess')
router.register(r'sitebranding', SiteBrandingViewSet, base_name='sitebranding')
urlpatterns = router.urls

""" API v1 URLs. """
from rest_framework.routers import DefaultRouter

from .views import JournalAccessViewSet, UserPageVisitViewSet

router = DefaultRouter()
router.register(r'journalaccess', JournalAccessViewSet, base_name='journalaccess')
router.register(r'userpagevisit', UserPageVisitViewSet, base_name='userpagevisit')
urlpatterns = router.urls

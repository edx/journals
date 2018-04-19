""" API v1 URLs. """
from rest_framework.routers import DefaultRouter

from .views import JournalAccessViewSet

router = DefaultRouter()
router.register(r'journalaccess', JournalAccessViewSet, base_name='journalaccess')
urlpatterns = router.urls

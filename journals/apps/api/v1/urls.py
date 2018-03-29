""" API v1 URLs. """
from django.conf.urls import url

from .views import JournalAccessViewSet

urlpatterns = [
    url(r'^journalaccess', JournalAccessViewSet.as_view({'post': 'create',})),
]
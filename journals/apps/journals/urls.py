"""
Journals URLs.
"""
from django.conf.urls import url

from journals.apps.journals import video_chooser as video_chooser_views

urlpatterns = [
    url(r'^video_chooser/$', video_chooser_views.chooser, name='video_chooser'),
    url(r'^video_chooser/(\d+)/$', video_chooser_views.video_chosen, name='video_chosen'),
]

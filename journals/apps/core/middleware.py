"""
Journals core middleware module
"""
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from wagtail.wagtailcore.models import Site


class SettingsOverrideMiddleware(object):
    def process_request(self, request):
        """
        Overrides django settings based on request
        """
        try:
            site = Site.find_for_request(request)
            setattr(settings, 'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL', site.siteconfiguration.from_email)
        except ObjectDoesNotExist:
            pass
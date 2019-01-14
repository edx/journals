""" API for theming / site branding """
from urllib.parse import urlparse

from django_filters.rest_framework import DjangoFilterBackend
import waffle
from rest_framework import views, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from journals.apps.api.serializers import UserSerializer, UserPageVisitSerializer
from journals.apps.api.v1.theming.filters import SiteBrandingFilter
from journals.apps.api.v1.theming.serializers import SiteBrandingSerializer
from journals.apps.core.models import SiteConfiguration, User
from journals.apps.journals.models import JournalAccess, UserPageVisit
from journals.apps.journals.utils import get_image_url
from journals.apps.theming.models import SiteBranding
from journals.apps.journals.utils import lms_integration_enabled

STANDARD_HTTP_PORTS = [80, 443]
DISABLE_LMS_WAFFLE_SWITCH = 'disable_lms_integration'


class SiteBrandingViewSet(viewsets.ReadOnlyModelViewSet):
    """ API for SiteBranding model """
    serializer_class = SiteBrandingSerializer
    queryset = SiteBranding.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filter_class = SiteBrandingFilter
    permission_classes = (AllowAny, )


class SiteInformationView(views.APIView):
    """
    API designed to be first hit by client. Will contain theming, current user, and site information
    """
    permission_classes = (AllowAny, )

    def get_last_visited(self, user):
        """ Returns the the last visited page per journal per user"""
        user_visits = UserPageVisit.objects.filter(user=user)
        visited_journal_about_ids = user_visits.values_list('journal_about', flat=True).distinct()
        return [
            user_visits.filter(journal_about_id=about_id).order_by("-visited_at").first()
            for about_id
            in visited_journal_about_ids
        ]

    def get(self, request):
        """ Responds to GET calls with theming, user, and site information """
        if request.user.is_authenticated:
            current_user = User.objects.get(pk=self.request.user.pk)
        else:
            current_user = None
        frontend_url = request.META.get('HTTP_REFERER')
        frontend_url = urlparse(frontend_url)._replace(path='').geturl()
        try:
            site_config = SiteConfiguration.objects.get(frontend_url=frontend_url)
            site = site_config.site
        except SiteConfiguration.DoesNotExist:
            site = request.site

        server_url = "{}://{}".format(
            request.scheme,
            site.hostname,
        )
        port = request.get_port()
        if port not in STANDARD_HTTP_PORTS:
            server_url += ':{}'.format(port)
        logo = get_image_url(site, site.sitebranding.site_logo) if site.sitebranding.site_logo else None
        theme_name = site.sitebranding.theme_name
        lms_url_root = site.siteconfiguration.lms_public_url_root_override or site.siteconfiguration.lms_url_root
        footer_links = site.sitebranding.footer_links
        authorized_journals = JournalAccess.get_user_accessible_journal_ids(request.user)
        segment_key = site.siteconfiguration.segment_key
        last_visited = self.get_last_visited(self.request.user) if self.request.user.is_authenticated else []

        return Response({
            'user': UserSerializer(current_user).data,
            'is_authenticated': bool(current_user),
            'visited_pages': UserPageVisitSerializer(last_visited, many=True).data,
            'server_url': server_url,
            'logo': logo,
            'theme_name': theme_name,
            'lms_url_root': lms_url_root,
            'footer_links': footer_links,
            'authorized_journals': authorized_journals,
            'segment_key': segment_key,
            'lms_integration': lms_integration_enabled(),
        })

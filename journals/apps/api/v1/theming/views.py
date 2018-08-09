""" API for theming / site branding """
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from journals.apps.api.v1.theming.filters import SiteBrandingFilter
from journals.apps.api.v1.theming.serializers import SiteBrandingSerializer
from journals.apps.theming.models import SiteBranding


class SiteBrandingViewSet(viewsets.ReadOnlyModelViewSet):
    """ API for SiteBranding model """
    serializer_class = SiteBrandingSerializer
    queryset = SiteBranding.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filter_class = SiteBrandingFilter
    permission_classes = (AllowAny, )

""" Filter class for theming / site branding """
from django_filters import rest_framework as filters

from journals.apps.theming.models import SiteBranding


class SiteBrandingFilter(filters.FilterSet):
    """ Filter for SiteBranding """
    site_name = filters.CharFilter(name='site__site_name')
    hostname = filters.CharFilter(name='site__hostname')

    class Meta:
        model = SiteBranding
        fields = [
            'theme_name',
            'site_name',
            'hostname',
        ]

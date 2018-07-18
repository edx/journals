""" Filter class for theming / site branding """
from django_filters import rest_framework as filters

from journals.apps.theming.models import SiteBranding
from journals.apps.core.models import SiteConfiguration


class SiteBrandingFilter(filters.FilterSet):
    """ Filter for SiteBranding """
    frontend_url = filters.CharFilter(name='frontend_url', method='filter_frontend_url')

    def filter_frontend_url(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        Return SiteBranding records associated with SiteConfigurations with this frontend_url
        """
        # SiteBranding is associated with a Site and a SiteConfiguration is associated with a Site.
        # Find the SiteConfiguration with this frontend_url.
        # 'frontend_url' is a unique field so there should only by one site_configuration
        site_configuration = SiteConfiguration.objects.get(frontend_url=value)

        # Return the SiteBranding associated with the same Site.
        return queryset.filter(site_id=site_configuration.site_id)

    class Meta:
        model = SiteBranding
        fields = [
            'frontend_url'
        ]

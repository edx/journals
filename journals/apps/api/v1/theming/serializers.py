""" Theming / Site Branding Serializers"""
from rest_framework import serializers

from journals.apps.theming.models import SiteBranding
from journals.apps.journals.models import JournalImage


class SiteLogoSerializer(serializers.ModelSerializer):
    """
    Serializer for the site logo associated with a site brand
    """

    class Meta(object):
        model = JournalImage
        fields = (
            'title',
            'file',
        )


class SiteBrandingSerializer(serializers.ModelSerializer):
    """
    Serializer for the ```SiteBranding``` model.
    """
    site_logo = SiteLogoSerializer(many=False, read_only=True)

    class Meta(object):
        model = SiteBranding
        read_only = True
        fields = (
            'theme_name',
            'site_logo'
        )

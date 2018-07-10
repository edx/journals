""" Theming / Site Branding Serializers"""
from rest_framework import serializers
from wagtail.wagtailcore.models import Site
from wagtail.wagtailimages.models import Image

from journals.apps.theming.models import SiteBranding


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer for the site associated with a site brand
    """

    class Meta(object):
        model = Site
        fields = (
            'site_name',
            'hostname',
        )


class SiteLogoSerializer(serializers.ModelSerializer):
    """
    Serializer for the site logo associated with a site brand
    """

    class Meta(object):
        model = Image
        fields = (
            'title',
            'file',
        )


class SiteBrandingSerializer(serializers.ModelSerializer):
    """
    Serializer for the ```SiteBranding``` model.
    """
    site_logo = SiteLogoSerializer(many=False, read_only=True)
    site = SiteSerializer(many=False, read_only=True)

    class Meta(object):
        model = SiteBranding
        read_only = True
        fields = (
            'theme_name',
            'site_logo',
            'site'
        )

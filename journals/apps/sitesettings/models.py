'''Models for Site-Aware Settings'''
from django.db import models
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting


@register_setting
class SiteBranding(BaseSetting):
    site_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    theme_name = models.CharField(max_length=128, blank=True, default='')

    panels = [
        FieldPanel('theme_name'),
        ImageChooserPanel('site_logo'),
    ]

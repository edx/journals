'''Models for Site-Aware Settings'''
from django.db import models
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from jsonfield.fields import JSONField


@register_setting
class SiteBranding(BaseSetting):
    '''Model that contains branding related attributes'''
    site_logo = models.ForeignKey(
        'journals.JournalImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    theme_name = models.CharField(max_length=128, blank=True, default='')

    footer_links = JSONField(
        verbose_name='Footer Links',
        help_text="""JSON should be in the format:
                     [
                       {
                         "label_text": "Link Name 1",
                         "destination_link": "link_url_1"
                       },
                       {
                         "label_text": "Link Name 2",
                         "destination_link": "link_url_2"
                       },
                    ]""",
        null=False,
        blank=False,
        default=[
            {
                "label_text": "FAQ",
                "destination_link": "http://www.example.com/",
            },
            {
                "label_text": "Contact Us",
                "destination_link": "http://www.example.com/",
            }
        ]
    )

    panels = [
        FieldPanel('theme_name'),
        ImageChooserPanel('site_logo'),
        FieldPanel('footer_links'),
    ]

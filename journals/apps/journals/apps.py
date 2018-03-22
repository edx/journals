"""
App Configuration for Journals
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from django.apps import AppConfig


class JournalsAppConfig(AppConfig):
    """
    App Configuration for Completion
    """
    name = 'journals.apps.journals'
    verbose_name = 'Journals'

    def ready(self):
        from . import handlers  # pylint: disable=unused-variable

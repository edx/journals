"""
App Configuration for core
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    """
    App Configuration for core
    """
    name = 'journals.apps.core'
    verbose_name = 'Core'

    def ready(self):
        from . import handlers  # pylint: disable=unused-variable

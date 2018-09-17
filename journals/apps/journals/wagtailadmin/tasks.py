"""
Module to define background tasks for wagtail admin related features
"""
import logging

from background_task import background
from django.core import management
from django.core.management import CommandError

log = logging.getLogger(__name__)


@background(schedule=30)
def task_run_management_command(command):
    """
    Task to run management command
    """

    try:
        management.call_command(command)
        log.info("Command %s successully executed.", command)
    except CommandError as ex:
        log.exception("Failed to executed %s command, Error: %s ", command, str(ex))

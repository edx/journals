"""
    importing all journal/admin/ module files here, as django reads admin classes form here only.
"""

from .django_admin import *  # pylint: disable=wildcard-import
from ..wagtailadmin.admin import *  # pylint: disable=wildcard-import

import logging
from os import environ
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from journals.apps.core.models import SiteConfiguration

logger = logging.getLogger(__name__)


def get_env_setting(setting):
    """ Get the environment setting or raise exception """
    try:
        return environ[setting]
    except KeyError:
        error_msg = "Set the [%s] env variable!" % setting
        raise ImproperlyConfigured(error_msg)


def get_whitelist_domains(request):
    """
        Extracts and returns domain list from siteconfiguration urls, including the domain on which server is running.
    """
    (_, request_domain, _, _, _) = urlsplit(request.build_absolute_uri())
    permitted_domains = [request_domain]
    try:
        for key, value in request.site.siteconfiguration.__dict__.items():
            if "url" in key.lower() and type(value) == str:
                (_, domain, _, _, _) = urlsplit(value)
                permitted_domains.append(domain)
    except SiteConfiguration.DoesNotExist as e:
        logger.exception(e)
    return permitted_domains

"""
Utility methods for journals
"""
import logging
import requests

from slumber.exceptions import HttpNotFoundError, HttpClientError
from journals.apps.journals.utils import lms_integration_enabled

logger = logging.getLogger(__name__)


def get_discovery_journal(api_client, uuid=None):
    """
    Get Journals from discovery
    :param api_client: discovery api client
    :param uuid: one or many comma separated UUIDs
    """
    if not lms_integration_enabled():
        return []

    if uuid:
        return api_client.journals.get(uuid=uuid)['results']
    return api_client.journals.get()['results']


def update_service(client, uuid, data, service_name):
    """
        Updates Journal to other services
    :param client: relevant client
    :param uuid: uuid of Journal
    :param data: data (body) to update
    :param service_name: e.g : ecommerce or discovery
    """
    if lms_integration_enabled():
        try:
            client.journals(uuid).patch(data)
            return True
        except HttpNotFoundError as err:
            # Only a WARN because this will often happen on JournalAboutPage creation.
            logging.warning("Unable to update {service_name} because UUID doesn't exist: {error}".format(
                service_name=service_name,
                error=err.content
            ))
        except HttpClientError as err:
            logging.error("Error updating {service_name} after JournalAboutPage publish: {error}".format(
                service_name=service_name,
                error=err.content
            ))
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(
                'Could not update journal uuid={uuid} in {service_name} service, err={err}'.format(
                    uuid=uuid, service_name=service_name, err=conn_err
                ))

    return False


def delete_from_service(client, uuid, service_name):
    """
        Deletes Journal from other services
    :param client: relevant client
    :param uuid: uuid of Journal
    :param service_name: e.g : ecommerce or discovery
    """
    if lms_integration_enabled():
        try:
            client.journals(uuid).delete()
            return True
        except HttpNotFoundError as err:
            # Only a WARN because this will often happen on JournalAboutPage creation.
            logging.warning("Unable to Delete Journal from {service_name} because UUID doesn't exist: {error}".format(
                service_name=service_name,
                error=err.content
            ))
        except HttpClientError as err:
            logging.error("Error updating Journal from {service_name} after JournalAboutPage publish: {error}".format(
                service_name=service_name,
                error=err.content
            ))

    return False

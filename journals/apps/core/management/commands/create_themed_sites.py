""" This command creates Sites, SiteThemes, SiteConfigurations and partners."""

import fnmatch
import json
import logging
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Creates Sites, SiteThemes, and SiteConfigurations."""

    help = 'Creates Sites, SiteThemes, and SiteConfigurations'
    dns_name = None
    theme_path = None
    configuration_filename = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--dns-name",
            type=str,
            help="Enter DNS name of sandbox.",
            required=True
        )

        parser.add_argument(
            "--theme-path",
            type=str,
            help="Enter theme directory path",
            required=True
        )

        parser.add_argument(
            "--port",
            help="Port number for site",
            required=True
        )

        parser.add_argument(
            "--devstack",
            action='store_true',
            help="Use devstack config, otherwise sandbox config is assumed",
        )

    def _create_site(self, site_data, port):
        """
        Create Sites including SiteConfigurations and Branding
        """

        call_command(
            'create_site',
            '--sitename', site_data.get('sitename'),
            '--hostname', site_data.get('hostname'),
            '--port', port,
            '--lms-url-root', site_data.get('lms_base_url'),
            '--lms-public-url-root-override', site_data.get('lms_public_base_url'),
            '--discovery-api-url', site_data.get('discovery_api_url'),
            '--ecommerce-api-url', site_data.get('ecomm_api_url'),
            '--discovery-partner-id', site_data.get('discovery_partner_short_code'),
            '--ecommerce-partner-id', site_data.get('ecomm_partner_short_code'),
            '--currency-codes', site_data.get('currency_codes'),
            '--client-secret', site_data.get('oauth_settings', {}).get('SOCIAL_AUTH_EDX_OIDC_SECRET'),
            '--client-id', site_data.get('oauth_settings', {}).get('SOCIAL_AUTH_EDX_OIDC_KEY'),
            '--discovery-journal-api-url', site_data.get('discovery_api_url_for_journal'),
            '--ecommerce-journal-api-url', site_data.get('ecomm_journal_api_url'),
            '--ecommerce-public-url-root', site_data.get('ecomm_public_base_url'),
            '--theme-name', site_data.get('theme_dir_name')
        )

    def _create_org(self, site_data):
        call_command(
            'create_org',
            '--key', site_data.get('organization'),
            '--sitename', site_data.get('sitename')
        )

    def find(self, pattern, path):
        """
        Matched the given pattern in given path and returns the list of matching files
        """
        result = []
        for root, dirs, files in os.walk(path):  # pylint: disable=unused-variable
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    result.append(os.path.join(root, name))
        return result

    def _get_site_partner_data(self):
        """
        Reads the json files from theme directory and returns the site partner data in JSON format.
        """
        site_data = {}
        for config_file in self.find(self.configuration_filename, self.theme_path):
            logger.info('Reading file from %s', config_file)
            configuration_data = json.loads(
                json.dumps(
                    json.load(
                        open(config_file)
                    )
                ).replace("{dns_name}", self.dns_name)
            )['journals_configuration']

            sitename = configuration_data.get('sitename')
            if sitename:
                site_data[sitename] = configuration_data

        return site_data

    def handle(self, *args, **options):
        if options['devstack']:
            configuration_prefix = 'devstack'
        else:
            configuration_prefix = 'sandbox'

        port = options['port']

        self.configuration_filename = '{}_configuration.json'.format(configuration_prefix)
        self.dns_name = options['dns_name']
        self.theme_path = options['theme_path']

        logger.info("Using %s configuration...", configuration_prefix)
        logger.info('DNS name: %s', self.dns_name)
        logger.info('Theme path: %s', self.theme_path)

        all_sites = self._get_site_partner_data()
        for site_name, site_data in all_sites.items():
            logger.info('Creating %s Site', site_name)
            self._create_site(site_data, port)
            if site_data.get('organization'):
                logger.info('Creating %s Organization', site_data.get('organization'))
                self._create_org(site_data)

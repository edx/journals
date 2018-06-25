'''Create Site management command'''
from django.core.management.base import BaseCommand
from wagtail.core.models import Site

from journals.apps.journals.models import Organization


class Command(BaseCommand):
    '''Management Command for creating organization'''
    help = 'Creates a new organization in the journals app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            help='Org key (no spaces)',
            required=True
        )
        parser.add_argument(
            '--sitename',
            help='Organization full name',
            required=True
        )

    def handle(self, *args, **options):
        """
        Creates a new organization if one does not already exist with that key.
        """
        # Required fields
        org_key = options['key']
        sitename = options['sitename']

        # Get site by site name and exit if it doesn't exist
        try:
            site = Site.objects.get(site_name=sitename)
        except Site.DoesNotExist:
            self.stderr.write("Organization creation failed: Site with name `{}` does not exist".format(sitename))
            return

        # Check if org already exists
        try:
            org = Organization.objects.get(name=org_key)
        except Organization.DoesNotExist:
            org = None

        if org:
            self.stderr.write("Organization creation failed: Org already exists with key `{}`".format(org_key))
            return

        # Create org in journals
        org = Organization.objects.create(
            name=org_key,
            site=site,
        )
        self.stdout.write("Organization `{}` successfully created".format(org_key))

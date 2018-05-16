'''Create Site management command'''
from urllib.parse import urljoin

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from journals.apps.journals.models import JournalIndexPage
from journals.apps.core.models import SiteConfiguration
from journals.apps.theming.models import SiteBranding

from wagtail.wagtailcore.models import Page, Site, Collection, GroupPagePermission, GroupCollectionPermission

PERMISSIONS = {
    'Editors': {
        'page_permissions': ['add', 'edit'],
        'collection_permissions': [
            'add_image', 'change_image',
            'add_document', 'change_document'
        ],
        'core_permissions': ['access_admin']
    },
    'Moderators': {
        'page_permissions': ['add', 'edit', 'publish'],
        'collection_permissions': [
            'add_image', 'change_image', 'delete_image',
            'add_document', 'change_document', 'delete_document'
        ],
        'core_permissions': ['access_admin', 'change_sitebranding']
    }
}


class Command(BaseCommand):
    '''Management Command for creating site'''
    help = 'Creates a new site and all necessary additional configs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sitename',
            help='Name of new site',
            required=True
        )
        parser.add_argument(
            '--hostname',
            help='Hostname of new site (e.g. journals.example.com)',
            required=True
        )
        parser.add_argument(
            '--port',
            help='Webserver port to listen to',
            required=True
        )
        parser.add_argument(
            '--lms-root-url',
            help='Root URL for LMS for API calls'
        )
        parser.add_argument(
            '--lms-public-root-url',
            help='Public facing root URL for LMS (only needed if different than lms-root-url'
        )
        parser.add_argument(
            '--discovery-api-url',
            help='Discovery api endpoint'
        )
        parser.add_argument(
            '--ecommerce-api-url',
            help='Ecommerce api endpoint'
        )
        parser.add_argument(
            '--discovery-partner-id',
            help='Discovery service partner short code'
        )
        parser.add_argument(
            '--ecommerce-partner-id',
            help='Ecommerce service partner short code'
        )
        parser.add_argument(
            '--currency-codes',
            help='Comma separated list of currency codes'
        )
        parser.add_argument(
            '--client-secret',
            help='OAuth client secret'
        )
        parser.add_argument(
            '--client-id',
            help='OAuth client key'
        )
        parser.add_argument(
            '--discovery-journal-api-url',
            help='Journal endpoint of discovery (defaults to /journal/api/v1 on discovery domain)'
        )
        parser.add_argument(
            '--ecommerce-journal-api-url',
            help='Journal endpoint of ecommerce (defaults to /journal/api/v1 on ecommerce domain)'
        )
        parser.add_argument(
            '--ecommerce-public-url-root',
            help='Ecommerce public root url'
        )

    def create_index_page(self, sitename):
        '''create_index_page'''
        root_page = Page.get_root_nodes()[0]
        index_page = JournalIndexPage(
            title="{} Index Page".format(sitename),
            intro="{} introduction".format(sitename)
        )
        root_page.add_child(instance=index_page)
        index_page.save_revision().publish()
        return index_page

    def build_oauth_settings(
        self,
        client_id,
        client_secret,
        lms_root_url,
        lms_public_root_url
    ):
        ''' Builds JSON based OAuth settings for site config '''

        # If public url isn't provided (because it's the same), use normal root url
        lms_public_root_url = lms_public_root_url or lms_root_url

        settings = {
            "SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY": client_secret,
            "SOCIAL_AUTH_EDX_OIDC_SECRET": client_secret,
            "SOCIAL_AUTH_EDX_OIDC_URL_ROOT": urljoin(lms_root_url, '/oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_ISSUER": urljoin(lms_root_url, '/oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_KEY": client_id,
            "SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT": urljoin(lms_public_root_url, 'oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL": urljoin(lms_public_root_url, 'logout'),
            "SOCIAL_AUTH_EDX_OIDC_ISSUERS": [
                lms_root_url
            ]
        }
        return settings

    def create_site_config(self, site, options):
        '''
        Creates a site config for a site. If a site config already exists in the DB, it copies
        the values to use as default values. It then overwrites any values with command line
        overrides in `options`.
        '''
        # All optional fields
        oauth_settings = self.build_oauth_settings(
            options.get('client-id', 'journals-key-' + site.site_name),
            options.get('client-secret', 'journals-secret-' + site.site_name),
            options.get('lms-root-url', ''),
            options.get('lms-public-root-url', ''),
        )

        # If the journal endpoint isn't provided, fallback on rewriting the discovery endpoint with the journal path
        discovery_journal_api_url = options.get(
            'discovery-journal-api-url',
            urljoin(options.get('discovery-api-url', ''), '/journal/api/v1')
        )

        # Same as above, but with ecommerce.
        ecommerce_journal_api_url = options.get(
            'ecommerce-journal-api-url',
            urljoin(options.get('ecommerce-api-url', ''), '/journal/api/v1')
        )

        fields = {
            'lms_root_url': options.get('lms-root-url'),
            'lms_public_root_url': options.get('lms-public-root-url'),
            'discovery_api_url': options.get('discovery-api-url'),
            'ecommerce_api_url': options.get('ecommerce-api-url'),
            'discovery_partner_id': options.get('discovery-partner-id'),
            'ecommerce_partner_id': options.get('ecommerce-partner-id'),
            'currency_codes': options.get('currency-codes'),
            'oauth_settings': oauth_settings,
            'discovery_journal_api_url': discovery_journal_api_url,
            'ecommerce_journal_api_url': ecommerce_journal_api_url,
            'ecommerce_public_root_url': options.get('ecommerce-public-root-url'),
        }

        # If another site config exists, use it's values as defaults
        site_configs = SiteConfiguration.objects.all()
        if site_configs:
            site_config = site_configs[0]
            site_config.pk = None
            site_config.site = site
        else:
            site_config = SiteConfiguration(site=site)

        for key in fields:
            if fields[key]:
                setattr(site_config, key, fields[key])

        site_config.save()

    def create_collection(self, name):
        '''create_collection'''
        root_collection = Collection.get_first_root_node()
        collection = Collection(
            name=name
        )
        root_collection.add_child(instance=collection)
        collection.save()
        return collection

    def add_group_permissions_by_codename(self, group, codename, page=None, collection=None):
        """
            Adds all permissions to groups based on PERMISSIONS dict above.
            Params:
                group : (Group) Group to add permissions to
                codename: (str) Name of permissions to assign
                page: (Page) Root page to give permission to (if provided)
                collection: (Collection) Collection to give group access to (if provided)

            NOTE: GroupPagePermission model takes a permission_type string instead of an actual permission. For
            simplicity, we are using the same `codename` field for this data even through it is not the `codename`
            field on a Permission model.
        """
        if page:
            GroupPagePermission.objects.create(
                group=group,
                page=page,
                permission_type=codename
            )
        elif collection:
            permission = Permission.objects.get(codename=codename)
            GroupCollectionPermission.objects.create(
                group=group,
                collection=collection,
                permission=permission
            )
        else:
            permission = Permission.objects.get(codename=codename)
            group.permissions.add(permission)

    def create_groups_and_permissions(self, name, index_page, collection):
        for role in PERMISSIONS:
            group = Group.objects.create(
                name=name + ' ' + role
            )
            for codename in PERMISSIONS[role]['page_permissions']:
                self.add_group_permissions_by_codename(group, codename, page=index_page)
            for codename in PERMISSIONS[role]['collection_permissions']:
                self.add_group_permissions_by_codename(group, codename, collection=collection)
            for codename in PERMISSIONS[role]['core_permissions']:
                self.add_group_permissions_by_codename(group, codename)

    @transaction.atomic
    def handle(self, *args, **options):
        """
        Creates a new Site complete with:
            - index page
            - site
            - site config
            - theming config
            - collection for documents and images
            - groups & permissions (collection names, root page, title)
        """
        # Required fields
        sitename = options['sitename']
        hostname = options['hostname']
        port = options['port']

        # Create Index Page
        index_page = self.create_index_page(sitename)

        # Create Site and set root to index page
        site = Site.objects.create(
            hostname=hostname,
            port=port,
            root_page=index_page,
            site_name=sitename
        )

        # Create site config
        self.create_site_config(site, options)

        # Create site branding with theme name
        SiteBranding.objects.create(
            site=site,
            theme_name=sitename
        )

        # Create collection for images and documents
        collection = self.create_collection(sitename)

        # Create groups and permissions based of PERMISSIONS data
        self.create_groups_and_permissions(
            sitename,
            index_page=index_page,
            collection=collection,
        )

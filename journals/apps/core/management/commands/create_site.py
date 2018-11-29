'''Create Site management command'''
from urllib.parse import urljoin

from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
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
            'add_video', 'change_video',
            'add_document', 'change_document'
        ],
        'core_permissions': ['access_admin', 'change_video']
    },
    'Moderators': {
        'page_permissions': ['add', 'edit', 'publish'],
        'collection_permissions': [
            'add_image', 'change_image', 'delete_image',
            'add_video', 'change_video', 'delete_video',
            'add_document', 'change_document', 'delete_document'
        ],
        'core_permissions': ['access_admin', 'change_sitebranding', 'change_video', 'delete_video']
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
            '--default-site',
            dest='default_site',
            action='store_true',
            help='Make this the default site'
        )

        parser.add_argument(
            '--lms-url-root',
            help='Root URL for LMS for API calls',
        )
        parser.add_argument(
            '--lms-public-url-root-override',
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
        parser.add_argument(
            '--theme-name',
            dest='theme_name',
            help='Name of theme to use'
        )
        parser.add_argument(
            '--frontend-url',
            help='Frontend app URL for Journals app',
        )
        parser.add_argument(
            '--org',
            help='Organization associated with the Site',
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
        lms_url_root,
        lms_public_url_root_override
    ):
        ''' Builds JSON based OAuth settings for site config '''
        settings = {
            "SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY": client_secret,
            "SOCIAL_AUTH_EDX_OIDC_SECRET": client_secret,
            "SOCIAL_AUTH_EDX_OIDC_URL_ROOT": urljoin(lms_url_root, '/oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_KEY": client_id,
            "SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT": urljoin(lms_public_url_root_override, 'oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL": urljoin(lms_public_url_root_override, 'logout'),
            "SOCIAL_AUTH_EDX_OIDC_ISSUER": urljoin(lms_url_root, '/oauth2'),
            "SOCIAL_AUTH_EDX_OIDC_ISSUERS": [lms_url_root],
        }
        return settings

    def create_site_config(self, site, options):
        '''
        Creates a site config for a site. If a site config already exists in the DB, it copies
        the values to use as default values. It then overwrites any values with command line
        overrides in `options`.
        '''
        # If another site config exists, use it's values as defaults
        site_configs = SiteConfiguration.objects.all()
        if site_configs:
            site_config = site_configs[0]
            site_config.pk = None
            site_config.site = site
        else:
            site_config = SiteConfiguration(site=site)

        lms_url_root = options.get('lms_url_root', site_config.lms_url_root)
        lms_public_url_root_override = options.get('lms_public_url_root_override', lms_url_root)

        oauth_settings = self.build_oauth_settings(
            client_id=options.get('client_id', 'journals-key-' + site.site_name),
            client_secret=options.get('client_secret', 'journals-secret-' + site.site_name),
            lms_url_root=lms_url_root,
            lms_public_url_root_override=lms_public_url_root_override
        )

        # If the journal endpoint isn't provided, fallback on rewriting the discovery endpoint with the journal path
        discovery_journal_api_url = options.get(
            'discovery_journal_api_url',
            urljoin(options.get('discovery_api_url', ''), '/journal/api/v1')
        )

        # Same as above, but with ecommerce.
        ecommerce_journal_api_url = options.get(
            'ecommerce_journal_api_url',
            urljoin(options.get('ecommerce_api_url', ''), '/journal/api/v1')
        )

        frontend_url = options.get('frontend_url', site_config.frontend_url)

        fields = {
            'lms_url_root': lms_url_root,
            'lms_public_url_root_override': lms_public_url_root_override,
            'discovery_api_url': options.get('discovery_api_url'),
            'ecommerce_api_url': options.get('ecommerce_api_url'),
            'discovery_partner_id': options.get('discovery_partner_id'),
            'ecommerce_partner_id': options.get('ecommerce_partner_id'),
            'currency_codes': options.get('currency_codes'),
            'oauth_settings': oauth_settings,
            'discovery_journal_api_url': discovery_journal_api_url,
            'ecommerce_journal_api_url': ecommerce_journal_api_url,
            'ecommerce_public_url_root': options.get('ecommerce_public_url_root'),
            'frontend_url': frontend_url,
        }

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
            - collection for documents, videos and images
            - groups & permissions (collection names, root page, title)
        """
        # Required fields
        sitename = options['sitename']
        hostname = options['hostname']
        port = options['port']
        theme_name = options['theme_name']
        default_site = options['default_site']
        if not theme_name:
            theme_name = sitename

        # Create Index Page
        index_page = self.create_index_page(sitename)

        # Create Site and set root to index page
        site = Site.objects.create(
            hostname=hostname,
            port=port,
            root_page=index_page,
            site_name=sitename,
            is_default_site=default_site,
        )

        # Create site config
        self.create_site_config(site, options)

        # Create site branding with theme name
        SiteBranding.objects.create(
            site=site,
            theme_name=theme_name
        )

        # Create collection for images, videos and documents
        collection = self.create_collection(sitename)

        # Create groups and permissions based of PERMISSIONS data
        self.create_groups_and_permissions(
            sitename,
            index_page=index_page,
            collection=collection,
        )

        # If organization specified, associate the site with it
        org = options.get('org', None)
        if org:
            call_command(
                'create_org',
                '--key', org,
                '--sitename', sitename
            )

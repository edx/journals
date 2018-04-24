# pylint: disable=missing-docstring
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


class Command(BaseCommand):  # pylint: disable=missing-docstring
    help = 'Creates a new site and all necessary additional configs'

    def add_arguments(self, parser):
        parser.add_argument('--sitename', help='Name of new site')  # MITxPRO or edX
        parser.add_argument('--hostname', help='Hostname of new site (e.g. journals.example.com)')
        parser.add_argument('--port', help='Webserver port to listen to')

    def create_index_page(self, sitename):  # pylint: disable=missing-docstring
        root_page = Page.get_root_nodes()[0]
        index_page = JournalIndexPage(
            title="{} Index Page".format(sitename),
            intro="{} introduction".format(sitename)
        )
        root_page.add_child(instance=index_page)
        index_page.save_revision().publish()
        return index_page

    def copy_site_config(self, site):
        """ Take first site config found, clone it and replace site """
        example_site_config = SiteConfiguration.objects.all()[0]
        example_site_config.pk = None
        example_site_config.site = site
        example_site_config.oauth_settings['SOCIAL_AUTH_EDX_OIDC_KEY'] = 'journals-key-' + site.site_name
        example_site_config.oauth_settings['SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY'] = 'journals-secret-' + site.site_name  # noqa pylint: disable=line-too-long
        example_site_config.oauth_settings['SOCIAL_AUTH_EDX_OIDC_SECRET'] = 'journals-secret-' + site.site_name
        example_site_config.save()

    def create_collection(self, name):  # pylint: disable=missing-docstring
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
        self.copy_site_config(site)

        # Create site branding with theme name
        site_branding = SiteBranding.objects.create(  # pylint: disable=unused-variable
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

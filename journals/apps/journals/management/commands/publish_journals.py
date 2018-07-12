'''management command to publish journals'''
from __future__ import unicode_literals

from hashlib import md5

from django.core.management.base import BaseCommand, CommandError
from journals.apps.journals.models import Journal, JournalIndexPage, JournalAboutPage, JournalMetaData
from slumber.exceptions import HttpClientError
from wagtail.wagtailcore.models import Page


class Command(BaseCommand):
    '''Base class for management command'''
    help = 'Publish Journal information to discovery and ecommerce'

    def add_arguments(self, parser):
        parser.add_argument('--create', help='The journal name')
        parser.add_argument('--org', help='Organization name (from journals-service)')
        parser.add_argument('--price', help='Journal price')
        parser.add_argument('--currency', default='USD', help='Journal currency')
        parser.add_argument('--access_length', type=int, default=365,
                            help='number of days to allow access')
        parser.add_argument('--delete', help='The journal uuid to delete')
        parser.add_argument('--publish', dest='publish', action='store_true',
                            help='Create the journal live and publish it live on site')
        parser.add_argument('--no-publish', dest='publish', action='store_false',
                            help='Create the journal but do not make it live on site')
        parser.set_defaults(publish=True)

    def _handle_create(self, options):
        '''handle creation of new Journal'''
        name = options['create']
        org = options['org']
        price = options['price']
        currency = options['currency']
        access_length = options['access_length']
        publish = options['publish']

        if not org:
            raise CommandError('--org <Org Name> must be specified')
        if not price:
            raise CommandError('--price <Journal price> must be specified')

        try:
            journal = Journal.objects.create_journal(name, org, access_length)
            journal_about_page = self._update_wagtail_pages(journal, create=True, publish=publish)

            journal_meta_data = JournalMetaData(
                journal_about_page,
                price=price,
                currency=currency,
                sku=self._create_sku(journal)
            )

        except Exception as err:
            raise CommandError('Error creating journal: {}'.format(err))

        try:
            self._update_discovery(
                journal.organization.site.siteconfiguration.discovery_journal_api_client,
                journal_meta_data.get_discovery_data()
            )
        except HttpClientError as err:
            # TODO - roll back journal updates if this fails
            raise CommandError('Error publishing to discovery-service: {}'.format(err.content))

        try:
            self._update_ecommerce(
                journal.organization.site.siteconfiguration.ecommerce_journal_api_client,
                journal_meta_data.get_ecommerce_data()
            )
        except HttpClientError as err:
            # TODO - roll back discovery updates if this fails
            raise CommandError('Error publishing to ecommerce-service: {}'.format(err.content))

        return journal

    def _update_wagtail_pages(self, journal, create=True, publish=True):
        '''create/update associated JournalIndexPage and JournalAboutPage'''
        site = journal.organization.site
        current_root = Page.objects.get(id=site.root_page_id)
        index_page = current_root.specific

        # if site root is not a JournalIndexPage, then create one and set it as site root
        if not isinstance(index_page, JournalIndexPage):
            # get base root page and add JournalIndexPage as child
            root_page = Page.get_root_nodes()[0]
            index_page = JournalIndexPage(
                title="{} Index Page".format(journal.organization.name),
                intro="{} introduction".format(journal.organization.name)
            )
            root_page.add_child(instance=index_page)

            if publish:
                index_page.save_revision().publish()

            # now set the site root page id to point to new_index_page
            site.root_page_id = index_page.id
            site.save()

        # create/update JournalAboutPage
        journal_about_page = index_page.get_first_child()
        if not create:
            if journal_about_page and isinstance(journal_about_page.specific, JournalAboutPage):
                journal_about_page.specific.journal = journal
                journal_about_page.specific.save()
        else:
            journal_about_page = JournalAboutPage(
                title=journal.name,
                journal=journal,
                short_description='{} description'.format(journal.name),
                long_description=''
            )
            index_page.add_child(instance=journal_about_page)
            if publish:
                journal_about_page.save_revision().publish()
            else:
                journal_about_page.unpublish()

        return journal_about_page

    def _create_sku(self, journal):
        '''create the sku for journal'''
        _hash = ' '.join((
            # TODO - are these the best fields to hash?
            str(journal.uuid),
            journal.organization.name
        )).encode('utf-8')

        md5_hash = md5(_hash.lower())
        digest = md5_hash.hexdigest()[-7:]
        return digest.upper()

    def _update_discovery(self, api_client, data, create=True):
        '''update the discovery service'''
        if create:
            results = api_client.journals.post(data)
            self.stdout.write(self.style.SUCCESS('Added record to discovery-service: {}'.format(results)))

    def _update_ecommerce(self, api_client, data, create=True):
        '''update the discovery service'''
        if create:
            results = api_client.journals.post(data)
            self.stdout.write(self.style.SUCCESS('Added record to ecommerce-service: {}'.format(results)))

    def _handle_delete(self, options):
        '''handle deletion of Journal'''
        uuid_val = options['delete']
        journal = Journal.objects.get(uuid=uuid_val)
        if journal:
            journal.delete()
        else:
            raise CommandError('The journal with uuid=%s could not be found', uuid_val)

        return journal

    def handle(self, *args, **options):
        """ publish journal info to required services """

        if options['create']:
            journal = self._handle_create(options)
            self.stdout.write(self.style.SUCCESS(
                'Successfully created Journal {} uuid={}').format(journal.name, journal.uuid))
        elif options['delete']:
            journal = self._handle_delete(options)
            self.stdout.write(self.style.SUCCESS(
                'Successfully deleted Journal {} uuid={}').format(journal.name, journal.uuid))
        else:
            raise CommandError('The proper arguments were not supplied to the command')

'''management command to publish journals'''
from __future__ import unicode_literals
import logging
from hashlib import md5

from django.core.management.base import BaseCommand, CommandError
from slumber.exceptions import HttpClientError, HttpServerError
from wagtail.wagtailcore.models import Page

from journals.apps.journals.models import Journal, JournalIndexPage, JournalAboutPage, JournalMetaData, Organization
from journals.apps.journals.api_utils import update_service, delete_from_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Base class for management command'''
    help = 'Publish Journal information to discovery and ecommerce'

    def add_arguments(self, parser):
        parser.add_argument('--create', help='The journal name')
        parser.add_argument('--update', help='Provide journal uuid, this will update the name and status of Journal to '
                                             'other services')
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
        price = options.get('price', '0')
        currency = options['currency']
        access_length = options['access_length']
        publish = options['publish']

        if not org:
            raise CommandError('--org <Org Name> must be specified')

        try:
            journal, _ = Journal.objects.get_or_create(name=name, organization=Organization.objects.get(name=org),
                                                       defaults={'access_length': access_length})
            journal_about_page = self._update_wagtail_pages(journal, create=True)

            journal_meta_data = JournalMetaData(
                journal_about_page,
                price=price,
                currency=currency,
                sku=self._create_sku(journal),
                publish=publish,
            )

        except Exception as err:
            raise CommandError('Error creating journal: {}'.format(err))

        try:
            discovery_data = journal_meta_data.get_discovery_data()
            self._update_discovery(
                journal.organization.site.siteconfiguration.discovery_journal_api_client,
                discovery_data
            )
        except (HttpClientError, HttpServerError) as err:
            # TODO - roll back journal updates if this fails
            err_str = 'Error publishing to discovery-service, discovery data={discovery_data} err={err}'.format(
                discovery_data=discovery_data,
                err=err.content
            )
            logger.error(err_str)
            raise CommandError(err_str)

        try:
            ecomm_data = journal_meta_data.get_ecommerce_data()
            self._update_ecommerce(
                journal.organization.site.siteconfiguration.ecommerce_journal_api_client,
                ecomm_data
            )
        except (HttpClientError, HttpServerError) as err:
            # TODO - roll back discovery updates if this fails
            err_str = 'Error publishing to ecommerce-service, ecomm data={ecomm_data} err={err}'.format(
                ecomm_data=ecomm_data,
                err=err.content
            )
            logger.error(err_str)
            raise CommandError(err_str)

        return journal

    def _update_wagtail_pages(self, journal, create=True):
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
            journal_about_page.save_revision().publish()
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
            self.stdout.write('Added record to discovery-service: {}'.format(results))

    def _update_ecommerce(self, api_client, data, create=True):
        '''update the discovery service'''
        if create:
            results = api_client.journals.post(data)
            self.stdout.write('Added record to ecommerce-service: {}'.format(results))

    def _handle_delete(self, options):
        '''handle deletion of Journal'''
        uuid_val = options['delete']
        try:
            journal = Journal.objects.get(uuid=uuid_val)
        except Journal.DoesNotExist:
            raise CommandError('The journal with uuid=%s could not be found', uuid_val)

        configuration = journal.organization.site.siteconfiguration

        if delete_from_service(configuration.discovery_journal_api_client, journal.uuid, 'discovery'):
            self.stdout.write('Successfully Deleted Journal UUID {} from '.format(journal.uuid))
        else:
            self.stderr.write('Error in deleting journal UUID {} from discovery service.'.format(journal.uuid))

        if delete_from_service(configuration.ecommerce_journal_api_client, journal.uuid, 'ecommerce'):
            self.stdout.write('Successfully Deleted Journal UUID {} from ecommerce'.format(journal.uuid))
        else:
            self.stderr.write('Error in deleting journal UUID {} from ecommerce service.'.format(journal.uuid))

        try:
            # before deleting journal, try to delete its JournalAboutPage object
            journal.journalaboutpage.delete()
        except JournalAboutPage.DoesNotExist:
            pass

        journal.delete()

    def _handle_update(self, options):
        """handle update of Journal name and status"""
        uuid = options['update']
        publish = options['publish']

        try:
            journal = Journal.objects.get(uuid=uuid)
        except Journal.DoesNotExist:
            raise CommandError('The journal with uuid=%s could not be found', uuid)

        configuration = journal.organization.site.siteconfiguration

        discovery_data = {
            'status': 'active' if publish else 'inactive',
            'title': journal.name
        }
        if update_service(configuration.discovery_journal_api_client, journal.uuid, discovery_data, 'discovery'):
            self.stdout.write('Successfully updated discovery service for Journal UUID {}'.format(journal.uuid))
        else:
            self.stderr.write('Error in updating discovery service for Journal UUID {}'.format(journal.uuid))

        ecommerce_data = {'title': journal.name}
        if update_service(configuration.ecommerce_journal_api_client, journal.uuid, ecommerce_data, 'ecommerce'):
            self.stdout.write('Successfully Updated ecommerce service for Journal UUID {}'.format(journal.uuid))
        else:
            self.stderr.write('Error in updating ecommerce service for Journal UUID {}'.format(journal.uuid))

        return journal

    def handle(self, *args, **options):
        """ publish journal info to required services """

        if options['create']:
            journal = self._handle_create(options)
            self.stdout.write('Successfully created Journal {} uuid={}'.format(journal.name, journal.uuid))
        elif options['delete']:
            self._handle_delete(options)
        elif options['update']:
            self._handle_update(options)
        else:
            raise CommandError('The proper arguments were not supplied to the command')

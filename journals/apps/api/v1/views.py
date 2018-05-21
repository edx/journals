'''API for Journals'''
import logging
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django_filters.rest_framework import DjangoFilterBackend
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess
from journals.apps.api.serializers import JournalAccessSerializer
from journals.apps.api.filters import JournalAccessFilter
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

logger = logging.getLogger(__name__)


class JournalAccessViewSet(viewsets.ModelViewSet):
    '''API for JournalAccess model'''
    lookup_field = 'uuid'
    queryset = JournalAccess.objects.all().order_by('-created')
    serializer_class = JournalAccessSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAdminUser,)
    filter_class = JournalAccessFilter

    def create(self, request, *args, **kwargs):
        '''create a JournalAccess entry'''
        username = request.data.get('user')
        journal_uuid = request.data.get('journal')
        order_number = request.data.get('order_number', None)
        revoke_access = request.data.get('revoke_access', 'false').lower() == 'true'
        if revoke_access:
            return self._revoke_access(order_number)

        try:
            user = User.objects.get(username=username)
            journal = Journal.objects.get(uuid=journal_uuid)
        except User.DoesNotExist:
            # TODO: should be warning or error level?
            logger.info("Could not grant access to user [%s], user does not exist in journals service", username)
            return HttpResponseBadRequest()

        except Journal.DoesNotExist:  # pylint: disable=duplicate-except
            logger.info("Could not grant access to journal [%s] for user [%s], journal does not exist",
                        journal_uuid, username)
            return HttpResponseBadRequest()

        JournalAccess.create_journal_access(user, journal, order_number)
        logger.info("User [%s] granted access to journal [%s]", username, journal)
        return HttpResponse()

    def _revoke_access(self, order_number):
        """ Revoke Access for the record with the given order_number """
        try:
            access_record = JournalAccess.revoke_journal_access(order_number=order_number)
        except JournalAccess.DoesNotExist:
            logger.info("Could not revoke access for order [%s], that order number does not exist", order_number)
            return HttpResponseNotFound()

        logger.info("Revoked access: user [%s], journal [%s], order number [%s]",
                    access_record.user,
                    access_record.journal,
                    access_record.order_number)
        return HttpResponse()

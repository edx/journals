'''API for Journals'''
import logging
from django.http import HttpResponse, HttpResponseBadRequest
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
    filter_class = JournalAccessFilter

    def create(self, request):
        '''create a JournalAccess entry'''
        order_number = request.data.get('order_number')
        username = request.data.get('user')
        journal_uuid = request.data.get('journal')
        try:
            user = User.objects.get(username=username)
            journal = Journal.objects.get(uuid=journal_uuid)
        except User.DoesNotExist:
            # TODO: should be warning or error level?
            logger.info("Could not grant access to user [%s], user does not exist in journals service", username)
            return HttpResponseBadRequest()

        except Journal.DoesNotExist:
            logger.info("Could not grant access to journal [%s] for user [%s], journal does not exist",
                        journal_uuid, username)
            return HttpResponseBadRequest()

        JournalAccess.create_journal_access(user, journal)
        logger.info("User [%s] granted access to journal [%s]", username, journal)
        return HttpResponse()

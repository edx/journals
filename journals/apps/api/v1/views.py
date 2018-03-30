# Create your views here.
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser

logger = logging.getLogger(__name__)


class JournalAccessViewSet(viewsets.GenericViewSet):

    # Disabled for now to make testing easier
    #permission_classes = [IsAdminUser]

    def create(self, request):
        order_number = request.data.get('order_number')
        username = request.data.get('user')
        journal_uuid = request.data.get('journal')
        try:
            user = User.objects.get(username=username)
            journal = Journal.objects.get(uuid=journal_uuid)
        except (User.DoesNotExist):
            # TODO: should be warning or error level?
            logger.info("Could not grant access to user [%s], user does not exist in journals service", username)
            return HttpResponseBadRequest()

        except (Journal.DoesNotExist):
            logger.info("Could not grant access to journal [%s] for user [%s], journal does not exist", journal_uuid, username)
            return HttpResponseBadRequest()

        JournalAccess.create_journal_access(user, journal)
        logger.info("User [%s] granted access to journal [%s]", username, journal)
        return HttpResponse()

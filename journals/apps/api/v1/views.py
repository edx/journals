""" API for Journals """

import logging

from collections import OrderedDict
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import generics

from journals.apps.api.filters import JournalAccessFilter, UserPageVisitFilter
from journals.apps.api.pagination import LargeResultsSetPagination
from journals.apps.api.permissions import UserPageVisitPermission
from journals.apps.api.serializers import JournalAccessSerializer, UserPageVisitSerializer, UserSerializer
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess, UserPageVisit


logger = logging.getLogger(__name__)


class JournalAccessViewSet(viewsets.ModelViewSet):
    """API for JournalAccess model"""
    lookup_field = 'uuid'
    queryset = JournalAccess.objects.all().order_by('-created')
    serializer_class = JournalAccessSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAdminUser,)
    filter_class = JournalAccessFilter
    pagination_class = LargeResultsSetPagination

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


class UserPageVisitView(generics.ListCreateAPIView):
    """API view for UserPageVisit model"""
    serializer_class = UserPageVisitSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserPageVisitFilter
    permission_classes = (IsAuthenticated, UserPageVisitPermission)

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UserPageVisit.objects.filter(user_id=user_id).order_by("-visited_at")


class ManualPageSerializerViewSet(viewsets.GenericViewSet):
    """
    This class is used as a template viewset and needed
    for manually serializing a JournalPage object (i.e. not through REST API)
    """
    def __init__(self, *args, **kwargs):
        super(ManualPageSerializerViewSet, self).__init__(*args, **kwargs)

        # seen_types is a mapping of type name strings (format: "app_label.ModelName")
        # to model classes. When an object is serialised in the API, its model
        # is added to this mapping. This is used by the Admin API which appends a
        # summary of the used types to the response.
        self.seen_types = OrderedDict()


class CurrentUserView(generics.RetrieveAPIView):
    """API view for the User model"""
    model = User
    serializer_class = UserSerializer

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)

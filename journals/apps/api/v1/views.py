""" API for Journals """

import logging

from django.contrib.auth import authenticate, login, logout
from collections import OrderedDict
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import views, viewsets, mixins, generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from journals.apps.api.filters import JournalAccessFilter, UserPageVisitFilter
from journals.apps.api.pagination import LargeResultsSetPagination
from journals.apps.api.permissions import UserPageVisitPermission
from journals.apps.api.serializers import JournalAccessSerializer, UserPageVisitSerializer, UserSerializer
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess, UserPageVisit


logger = logging.getLogger(__name__)


class UserAccountView(views.APIView):
    """
    API to create users, login and logout
    """
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        """create a user entry and log them in"""
        logout_only = request.data.get('logout')
        login_only = request.data.get('login')
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if logout_only:
            return self._handle_logout(request)

        if login_only:
            return self._handle_login(request, username, password)

        try:
            User.objects.create_user(username=username, email=email, password=password)
            return self._handle_login(request, username, password)
        except Exception as err:
            message = "Could not create user={} err={}".format(username, err)
            logger.error(message)
            return HttpResponseBadRequest(message)

    def _handle_login(self, request, username, password):
        try:
            authed_user = authenticate(request, username=username, password=password)
            login(request, authed_user)
            return Response({
                # 'user': UserSerializer(user).data,
                'username': UserSerializer(authed_user).data.get('username'),
                'email': UserSerializer(authed_user).data.get('email'),
                'is_authenticated': bool(authed_user.is_authenticated),
            })
        except Exception as err:
            message = "Login failed username={} err={}".format(username, err)
            logger.error(message)
            return HttpResponseBadRequest(message)

    def _handle_logout(self, request):
        try:
            logout(request)
            return Response({
                # 'user': UserSerializer(user).data,
                'username': '',
                'email': '',
                'is_authenticated': False,
            })
        except Exception as err:
            message = "Logout failed err={}".format(err)
            logger.error(message)
            return HttpResponseBadRequest(message)


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
        """create a JournalAccess entry"""
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
            logger.error("Could not grant access to user [%s], user does not exist in journals service", username)
            content = "User [{}] does not exist in journals service".format(username)
            return Response(content, status=status.HTTP_401_UNAUTHORIZED)

        except Journal.DoesNotExist:  # pylint: disable=duplicate-except
            logger.error(
                "Could not grant access to journal [%s] for user [%s], journal does not exist",
                journal_uuid,
                username
            )
            content = "Journal [{}] does not exist".format(journal_uuid)
            return Response(content, status=status.HTTP_404_NOT_FOUND)

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


class UserPageVisitViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """API for UserPageVisit model. Disabled `retrieve` and `destroy` by excluding their mixins"""
    serializer_class = UserPageVisitSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserPageVisitFilter
    permission_classes = (IsAuthenticated, UserPageVisitPermission)

    def get_queryset(self):
        """ Only return user's results unless user if staff """
        if self.request.user.is_staff:
            return UserPageVisit.objects.all().order_by("-visited_at")
        return UserPageVisit.objects.filter(user_id=self.request.user.id).order_by("-visited_at")

    def create(self, request, *args, **kwargs):
        """
        Overriding to allow POST calls to endpoint to create OR update. We want to update items by a combination
        of user_id and page_id POST data instead of the /<primary_key> URL pattern.
        """
        try:
            user = int(request.data.get('user'))
            page = int(request.data.get('page'))
        except ValueError:
            return HttpResponseBadRequest("Must supply user and page")

        try:
            visit = UserPageVisit.objects.get(user_id=user, page_id=page)
        except UserPageVisit.DoesNotExist:
            return super().create(request, *args, **kwargs)
        else:
            self.kwargs['pk'] = visit.id
            return super().update(request, *args, **kwargs)


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

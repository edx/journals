'''Filter class for Journals'''
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from journals.apps.journals.models import JournalAccess, JournalPage, UserPageVisit, Video


class JournalAccessFilter(filters.FilterSet):
    """Filter for JournalAccess"""
    user = filters.CharFilter(name='user__username')
    get_latest = filters.BooleanFilter(name='get_latest', method='filter_latest')
    ignore_revoked = filters.BooleanFilter(name='ignore_revoked', method='filter_revoked')
    block_id = filters.CharFilter(name='block_id', method='filter_xblock_id')

    def filter_revoked(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        If ignore_revoked is true, remove all revoked access records from queryset.
        """
        if value:
            return queryset.filter(revoked=False)
        else:
            return queryset

    def filter_latest(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        If a user has renewed their access to a given journal they may have multiple JournalAccess records for a
        given journal. If 'get_latest' is set to true, only return one JournalAccess record per journal per user.
        In other words, for a given user-journal pair there should only be one JournalAccess record returned.  In the
        case where a user-journal pair has multiple journal access records, return the access record with the latest
        expiration date.

        Args:
            queryset (QuerySet): queryset to be filtered
            value (Boolean): if True only return latest record per user-journal pair, else do no filtering

        Returns:
            filtered_queryset (QuerySet): filtered query sets
        """
        if not value:
            return queryset

        users = set(queryset.values_list('user', flat=True))
        filtered_uuids = []
        for user in users:
            user_queryset = queryset.filter(user=user)
            current_user_journals = set(user_queryset.values_list('journal', flat=True))
            for journal in current_user_journals:
                journal_queryset = user_queryset.filter(journal=journal)
                filtered_uuids.append(journal_queryset.order_by('-expiration_date').first().uuid)

        filtered_queryset = queryset.filter(uuid__in=filtered_uuids)
        return filtered_queryset

    def filter_xblock_id(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        Get the Journal from video block_id and then filter on journal.
        """
        if not value:
            return queryset
        qs = queryset
        try:
            journal_pages = JournalPage.objects.filter(videos=Video.objects.get(block_id=value))
            journal_uuids = [journal_page.get_journal().uuid for journal_page in journal_pages]
            qs = queryset.filter(journal__uuid__in=journal_uuids)
        except (JournalPage.DoesNotExist, Video.DoesNotExist):
            pass
        return qs

    class Meta:
        model = JournalAccess
        # user: returns access records only for that user
        # get_latest_journals: if true, only returns one journal access record per journal.
        #   selects journal with latest expiration date
        # ignore_revoked: if true, won't return access records that have been revoked
        fields = (
            'user',
            'get_latest',
            'ignore_revoked'
        )


class UserPageVisitFilter(filters.FilterSet):
    """ Filter for UserPageVisit """
    page_id = filters.CharFilter(name='page_id')
    user_id = filters.CharFilter(name='user_id')
    last_visit = filters.BooleanFilter(name='last_visit', method='get_last_visit')

    def get_last_visit(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        If last_visit is true, return the last page that user visited.
        """
        return [queryset.first()] if value else queryset

    class Meta:
        model = UserPageVisit
        fields = [
            'page_id',
            'user_id',
            'last_visit'
        ]


class PageAuthorizationFilter(BaseFilterBackend):
    """
    Filter that only allows user to see pages they have access to.
    """
    def filter_queryset(self, request, queryset, view):
        # TODO: Currently has additional DB calls for gettings authorized journals and authorized pages attached to
        # the journals. This happens on every API call
        authorized_journal_ids = JournalAccess.get_user_accessible_journal_ids(request.user)

        authorized_journal_page_ids = JournalPage.objects.filter(
            journal_about_page__journal__id__in=authorized_journal_ids
        ).values_list('id', flat=True)

        authorized_pages = (
            queryset.not_type(JournalPage) |
            queryset.type(JournalPage).filter(
                id__in=authorized_journal_page_ids
            )
        )

        return authorized_pages

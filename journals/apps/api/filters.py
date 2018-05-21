'''Filter class for Journals'''
from journals.apps.journals.models import JournalAccess
from django_filters import rest_framework as filters


class JournalAccessFilter(filters.FilterSet):
    '''Filter for JournalAccess'''
    user = filters.CharFilter(name='user__username')
    get_latest = filters.BooleanFilter(name='get_latest', method='filter_latest')
    ignore_revoked = filters.BooleanFilter(name='ignore_revoked', method='filter_revoked')

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

'''Filter class for Journals'''
from journals.apps.journals.models import JournalAccess
from django_filters import rest_framework as filters


class JournalAccessFilter(filters.FilterSet):
    user = filters.CharFilter(name='user__username')

    class Meta:
        model = JournalAccess
        fields = ('user',)

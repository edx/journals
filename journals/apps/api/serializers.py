""" Journal serializers """

from rest_framework import serializers

from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess, JournalAboutPage, Organization, UserPageVisit


class JournalAboutPageSerializer(serializers.ModelSerializer):
    """
    Serializer for JournalAboutPage
    """

    class Meta:
        model = JournalAboutPage
        fields = ('slug', 'card_image_absolute_url', 'short_description')


class JournalSerializer(serializers.ModelSerializer):
    """
    Serializer for Journal
    """
    journalaboutpage = JournalAboutPageSerializer(many=False, read_only=True)
    organization = serializers.SlugRelatedField(slug_field='name', queryset=Organization.objects.all())

    class Meta:
        model = Journal
        fields = (
            'name',
            'journalaboutpage',
            'organization'
        )


class JournalAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for the ``JournalAccess`` model.
    """
    journal = JournalSerializer(many=False, read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta(object):
        model = JournalAccess
        fields = (
            'uuid',
            'journal',
            'user',
            'expiration_date'
        )


class UserPageVisitSerializer(serializers.ModelSerializer):
    """
    Serializer for the "UserPageVisit" model.
    """

    class Meta(object):
        model = UserPageVisit
        fields = (
            'user',
            'page',
            'visited_at',
            'stale'
        )

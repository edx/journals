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
            'uuid',
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


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the "User" model.
    """
    visited_pages = UserPageVisitSerializer(many=True)

    class Meta(object):
        model = User
        fields = (
            'id',
            'username',
            'visited_pages',
        )


class SearchMetaDataSerializer(serializers.Serializer):
    """
    Serializer for SearchMetaData object
    """
    total_count = serializers.IntegerField()
    text_count = serializers.IntegerField()
    image_count = serializers.IntegerField()
    video_count = serializers.IntegerField()
    doc_count = serializers.IntegerField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class SearchHitSerializer(serializers.Serializer):
    """
    Serializer for SearchHit object (represents single hit)
    """
    page_id = serializers.IntegerField()
    page_title = serializers.CharField()
    page_path = serializers.CharField()
    journal_about_page_id = serializers.IntegerField()
    journal_id = serializers.IntegerField()
    journal_name = serializers.CharField()
    block_id = serializers.IntegerField()
    block_title = serializers.CharField()
    block_type = serializers.CharField()
    highlights = serializers.ListSerializer(child=serializers.CharField())
    score = serializers.CharField(max_length=200)
    span_id = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class SearchResultsSerializer(serializers.Serializer):
    """
    Serializer for SearchResults
    """
    meta = SearchMetaDataSerializer()
    hits = serializers.ListSerializer(child=SearchHitSerializer())

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

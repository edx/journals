""" Journal serializers """

from rest_framework import serializers

from journals.apps.core.models import User
from journals.apps.journals.models import (
    Journal,
    JournalAboutPage,
    JournalAccess,
    JournalPage,
    Organization,
    UserPageVisit
)


class JournalAboutPageSerializer(serializers.ModelSerializer):
    """
    Serializer for JournalAboutPage
    """

    class Meta:
        model = JournalAboutPage
        fields = ('id', 'card_image_absolute_url', 'short_description')


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

    def create(self, validated_data):
        page = validated_data.get('page')
        if isinstance(page.specific, JournalPage):
            journal_about = page.specific.get_journal_about_page()
            validated_data.update({'journal_about': journal_about})
            return UserPageVisit.objects.create(**validated_data)
        return UserPageVisit.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.page = validated_data.get('page', instance.page)
        instance.user = validated_data.get('user', instance.user)
        if isinstance(instance.page.specific, JournalPage):
            instance.journal_about = instance.page.specific.get_journal_about_page()
        instance.save()
        return instance

    class Meta(object):
        model = UserPageVisit
        fields = (
            'user',
            'page',
            'journal_about',
            'visited_at',
            'stale'
        )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the "User" model.
    """

    class Meta(object):
        model = User
        fields = (
            'id',
            'username',
            'can_access_admin',
            'email',
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
    breadcrumbs = serializers.ListSerializer(child=serializers.CharField())
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

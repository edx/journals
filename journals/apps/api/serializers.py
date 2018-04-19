'''Journal serializers'''
from rest_framework import serializers
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess


class JournalAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for the ``JournalAccess`` model.
    """
    journal = serializers.SlugRelatedField(slug_field='name', queryset=Journal.objects.all())
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta(object):
        model = JournalAccess
        fields = (
            'uuid',
            'journal',
            'user',
            'expiration_date'
        )

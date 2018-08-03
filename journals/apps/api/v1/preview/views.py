""" API to fetch Page preview """
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from journals.apps.api.permissions import WagtailAdminPermission


class PreviewView(APIView):
    """
    View to return Journal Previews via RestAPI.
    Will return a serialized Page object in the same
    format as fetching page from content api via
    /api/v1/content/pages
    """
    permission_classes = (WagtailAdminPermission, )

    def get(self, request, cache_key):  # pylint: disable=unused-argument
        """
        Get requested Page object from cache
        """
        if cache_key:
            data = cache.get(cache_key)
            if data:
                return Response(data)

        return Response(status=status.HTTP_404_NOT_FOUND)

""" API for to get Page preview from cache """
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_page_preview(request, cache_key):  # pylint: disable=unused-argument
    """
    Get requested Page object from cache
    """
    if cache_key:
        data = cache.get(cache_key)
        if data:
            return Response(data)

    return Response(status=status.HTTP_404_NOT_FOUND)

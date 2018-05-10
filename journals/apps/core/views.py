""" Core views. """
import logging
import uuid
from urllib.parse import unquote

from django.db import transaction, connection, DatabaseError
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import View

from journals.apps.core.constants import Status

logger = logging.getLogger(__name__)
User = get_user_model()


@transaction.non_atomic_requests
def health(_):
    """Allows a load balancer to verify this service is up.

    Checks the status of the database connection on which this service relies.

    Returns:
        HttpResponse: 200 if the service is available, with JSON data indicating the health of each required service
        HttpResponse: 503 if the service is unavailable, with JSON data indicating the health of each required service

    Example:
        >>> response = requests.get('https://journals.edx.org/health')
        >>> response.status_code
        200
        >>> response.content
        '{"overall_status": "OK", "detailed_status": {"database_status": "OK", "lms_status": "OK"}}'
    """

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        database_status = Status.OK
    except DatabaseError:
        database_status = Status.UNAVAILABLE

    overall_status = Status.OK if (database_status == Status.OK) else Status.UNAVAILABLE

    data = {
        'overall_status': overall_status,
        'detailed_status': {
            'database_status': database_status,
        },
    }

    if overall_status == Status.OK:
        return JsonResponse(data)
    else:
        return JsonResponse(data, status=503)


class AutoAuth(View):
    """Creates and authenticates a new User with superuser permissions.

    If the ENABLE_AUTO_AUTH setting is not True, returns a 404.
    """

    def get(self, request):
        """
        Create a new User.

        Raises Http404 if auto auth is not enabled.
        """
        if not getattr(settings, 'ENABLE_AUTO_AUTH', None):
            raise Http404

        username_prefix = getattr(settings, 'AUTO_AUTH_USERNAME_PREFIX', 'auto_auth_')

        # Create a new user with staff permissions
        username = password = username_prefix + uuid.uuid4().hex[0:20]
        User.objects.create_superuser(username, email=None, password=password)

        # Log in the new user
        user = authenticate(username=username, password=password)
        login(request, user)

        return redirect('/')


@login_required
def required_auth(request):
    """
    Used to require the user to log in through the journals service (thus
    creating an account in Journal for a new user) before being forwarded to
    the destination URL. This is necessary for verifying a user has an account
    in Journals so a purchase can be linked to that account.

    When generating a basket URL for a product that includes Journal access,
    it should be created via the following pattern:

    encoded_basket_url = urllib.parse.quote("<basket_url>")
    display_url = "<journals_domain>/require_auth?forward={}".format(encoded_basket_url)
    """
    # Quoted URL: http%3A//localhost%3A18130/basket/add/%3Fsku%3D8CF08E5
    forwarded_url = unquote(request.GET.get('forward'))
    return redirect(forwarded_url)

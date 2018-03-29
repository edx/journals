# Create your views here.
from django.http import JsonResponse
from journals.apps.core.models import User
from journals.apps.journals.models import Journal, JournalAccess
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser

class JournalAccessViewSet(viewsets.GenericViewSet):

    # Disabled for now to make testing easier
    #permission_classes = [IsAdminUser]

    def create(self, request):
        order_number = request.data.get('order_number')
        username = request.data.get('user')
        journal_uuid = request.data.get('journal')
        try:
            user = User.objects.get(username=username)
            journal = Journal.objects.get(uuid=journal_uuid)
        except (User.DoesNotExist, Journal.DoesNotExist) as e:
            return JsonResponse({'error':'invalid values'}, status=status.HTTP_400_BAD_REQUEST)

        access = JournalAccess.create_journal_access(user, journal)
        return JsonResponse({'access':access})

"""
Permissions for apps.api views
"""

from rest_framework import permissions


class UserPageVisitPermission(permissions.BasePermission):
    """
    Give permission whether user is allowed to see the page visit for a specific user.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_staff or request.user.id == int(view.kwargs['user_id'])
        )

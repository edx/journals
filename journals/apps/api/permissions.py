"""
Permissions for apps.api views
"""

from rest_framework import permissions


class UserPageVisitPermission(permissions.BasePermission):
    """
    Give permission whether user is allowed to see the page visit for a specific user.
    """

    def has_permission(self, request, view):
        """ Allows everything put posting visits for other users"""
        if request.user.is_staff or request.method != "POST":
            return True
        return True if int(request.data.get('user')) == request.user.id else False


class WagtailAdminPermission(permissions.BasePermission):
    """
    Checks whether given user has permission to access Wagtail Admin
    """

    def has_permission(self, request, view):
        return (
            request.user.can_access_admin
        )

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
        if request.user.is_staff or request.method == "GET":
            return True

        post_user = request.data.get('user')
        if request.method == "POST" and post_user and int(post_user) == request.user.id:
            return True

        return False


class WagtailAdminPermission(permissions.BasePermission):
    """
    Checks whether given user has permission to access Wagtail Admin
    """

    def has_permission(self, request, view):
        return (
            request.user.can_access_admin
        )

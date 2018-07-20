"""
Permissions for related to journals app
"""
from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.wagtailcore.permission_policies.collections import CollectionOwnershipPermissionPolicy

from journals.apps.journals.models import Video

video_permission_policy = CollectionOwnershipPermissionPolicy(Video, owner_field_name='source_course_run')


class VideoPermissionHelper(PermissionHelper):
    """
    Permission overrides for videos
    """
    def user_can_create(self, user):
        """
        Since video entries are imported from studio. We need to override this method to disable
        add button for videos
        """
        return False

    def user_can_edit_obj(self, user, obj):
        """
        Check if user has edit permissions on videos
        Since we are importing videos from studio we have to disable video `edit` feature
        in wagtail admin to keep video entries in sync with studio.
        To enable `edit` feature for videos we can use the code below
        return video_permission_policy.user_has_permission_for_instance(
            user, 'change', obj
        )
        """
        return False

    def user_can_delete_obj(self, user, obj):
        """
        Check if user has delete permissions on videos
        """
        return False

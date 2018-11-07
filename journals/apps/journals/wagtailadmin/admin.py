""" Journals admin module """

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from journals.apps.journals.models import (
    Journal,
    Video,
)
from journals.apps.journals.permissions import VideoPermissionHelper, JournalPermissionHelper
from journals.apps.journals.wagtailadmin.views import VideoIndexView, JournalIndexView, JournalAdminEditView, \
    JournalAdminCreateView, JournalAdminDeleteView


class VideoModelAdmin(ModelAdmin):
    """
    Video model admin
    """
    model = Video
    menu_label = 'Videos'
    menu_icon = 'media'
    menu_order = 400
    add_to_settings_menu = False
    exclude_from_explorer = False
    permission_helper_class = VideoPermissionHelper
    index_view_class = VideoIndexView
    form_fields_exclude = ('collection', 'block_id', 'source_course_run',)


class JournalModelAdmin(ModelAdmin):
    """
    Journal model admin
    """
    model = Journal
    menu_label = 'Journals'
    menu_icon = 'doc-full'
    menu_order = 1
    add_to_settings_menu = False
    exclude_from_explorer = False
    permission_helper_class = JournalPermissionHelper
    index_view_class = JournalIndexView
    edit_view_class = JournalAdminEditView
    create_view_class = JournalAdminCreateView
    delete_view_class = JournalAdminDeleteView


modeladmin_register(VideoModelAdmin)
modeladmin_register(JournalModelAdmin)

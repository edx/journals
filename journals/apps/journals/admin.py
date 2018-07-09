""" Journals admin module """
from django.contrib import admin

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register


from journals.apps.journals.models import (
    Journal,
    JournalAboutPage,
    JournalAccess,
    Organization,
    Video,
)
from journals.apps.journals.permissions import VideoPermissionHelper
from journals.apps.journals.views import VideoIndexView


# Custom admin pages
@admin.register(JournalAboutPage)
class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    fields = ('uuid', 'journalaboutpage', 'name', 'access_length', 'organization', 'video_course_ids')
    readonly_fields = ('uuid', 'journalaboutpage')


@admin.register(JournalAccess)
class JournalAccessAdmin(admin.ModelAdmin):
    fields = ('uuid', 'user', 'journal', 'expiration_date')
    readonly_fields = ('uuid',)


# Default admin pages below
admin.site.register(Organization)


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


modeladmin_register(VideoModelAdmin)

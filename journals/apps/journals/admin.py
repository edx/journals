""" Journals admin module """
from django.conf.urls import url
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
from journals.apps.journals.views import VideoIndexView, JournalAccessView


# Custom admin pages
@admin.register(JournalAboutPage)
class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    """
    Admin for Journal model.
    """
    fields = ('uuid', 'journalaboutpage', 'name', 'access_length', 'organization', 'video_course_ids')
    readonly_fields = ('uuid', 'journalaboutpage')

    def get_urls(self):
        my_urls = [
            url(
                r'(?P<journal_id>[0-9]+)/actions/import_users/',
                self.admin_site.admin_view(JournalAccessView.as_view()),
                name='import_users'
            ),
        ]
        return my_urls + super(JournalAdmin, self).get_urls()


@admin.register(JournalAccess)
class JournalAccessAdmin(admin.ModelAdmin):
    fields = ('uuid', 'user', 'journal', 'expiration_date')
    readonly_fields = ('uuid',)


# Default admin pages below
admin.site.register(Organization)
admin.site.register(Video)


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

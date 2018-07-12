""" Journals admin module """
import logging
import unicodecsv
from django.utils.translation import ugettext as _
from django.contrib import admin
from django.conf.urls import url

from .models import Journal, JournalAboutPage, JournalAccess, Organization
from .forms import UsersJournalAccessForm
from .views import JournalAccessView

from django.core.exceptions import ValidationError
from django_object_actions import DjangoObjectActions
from django.http import HttpResponseRedirect
from django.urls import reverse


logger = logging.getLogger(__name__)


# Custom admin pages
@admin.register(JournalAboutPage)
class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)


@admin.register(Journal)
class JournalAdmin(DjangoObjectActions, admin.ModelAdmin):
    change_actions = ('import_users',)
    fields = ('uuid', 'journalaboutpage', 'name', 'access_length', 'organization', 'video_course_ids')
    readonly_fields = ('uuid', 'journalaboutpage')

    def get_urls(self):
        my_urls = [
            url(
                r'(?P<journal_id>[0-9]+)/actions/import_users/',
                JournalAccessView.as_view(),
                name='import_users'
            ),
        ]
        return my_urls + super(JournalAdmin, self).get_urls()

    def import_users(self, request, journal):
        return HttpResponseRedirect(
            reverse('admin:import_users', args=[journal.id])
        )

    import_users.label = _("Import User's CSV")
    import_users.short_description = _(
        "Import User's CSV to add in this journal."
    )


@admin.register(JournalAccess)
class JournalAccessAdmin(admin.ModelAdmin):
    fields = ('uuid', 'user', 'journal', 'expiration_date')
    readonly_fields = ('uuid',)


# Default admin pages below
admin.site.register(Organization)

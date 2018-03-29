from django.contrib import admin
from .models import Journal, JournalAboutPage, JournalAccess, Organization

# Custom admin pages
@admin.register(JournalAboutPage)
class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    fields = ('uuid', 'journalaboutpage', 'name', 'access_length')
    readonly_fields = ('uuid', 'journalaboutpage')

@admin.register(JournalAccess)
class JournalAccessAdmin(admin.ModelAdmin):
    fields = ('uuid', 'user', 'journal', 'expiration_date', )
    readonly_fields = ('uuid',)

# Default admin pages below
admin.site.register(Organization)
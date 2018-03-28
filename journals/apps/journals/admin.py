from django.contrib import admin
from .models import Journal, JournalAboutPage, JournalAccess, Organization

# Custom admin pages
@admin.register(JournalAboutPage)
class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)

# Default admin pages below
admin.site.register(Journal)
admin.site.register(JournalAccess)
admin.site.register(Organization)

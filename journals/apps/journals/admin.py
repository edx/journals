from django.contrib import admin
from .models import Journal, JournalAboutPage

class JournalAboutPageAdmin(admin.ModelAdmin):
    fields = ('journal',)

admin.site.register(Journal)
admin.site.register(JournalAboutPage, JournalAboutPageAdmin)
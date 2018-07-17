"""
Forms and formsets related to journals
"""
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.forms import collection_member_permission_formset_factory

from journals.apps.journals.models import Video


GroupVideoPermissionFormSet = collection_member_permission_formset_factory(
    Video,
    [
        ('add_video', _("Add"), _("Add/edit videos you own")),
        ('change_video', _("Edit"), _("Edit any video")),
    ],
    'videos/video_permissions_formset.html'
)

"""
Forms and formsets related to journals
"""
from django import forms
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.forms import collection_member_permission_formset_factory

from journals.apps.journals.models import Video, Journal

GroupVideoPermissionFormSet = collection_member_permission_formset_factory(
    Video,
    [
        ('add_video', _("Add"), _("Add/edit videos you own")),
        ('change_video', _("Edit"), _("Edit any video")),
    ],
    'videos/video_permissions_formset.html'
)


class JournalEditForm(forms.ModelForm):
    """
        Journal Edit form for wagtail CMS
    """
    status = forms.BooleanField(label=_('Status'), required=False,
                                help_text=_('Used to determine whether journal is marketed or not.'))

    class Meta:
        model = Journal
        exclude = ('access_length', 'organization')


class JournalCreateForm(forms.ModelForm):
    """
        Journal Create form for wagtail CMS
    """
    price = forms.FloatField(label=_('Price'))
    currency = forms.CharField(label=_('Currency'))

    class Meta:
        model = Journal
        fields = '__all__'

    def __init__(self, request=None, *args, **kwargs):
        super(JournalCreateForm, self).__init__(*args, **kwargs)
        if request and not request.user.is_superuser:
            self.fields['organization'].queryset = self.fields['organization'].queryset.filter(site=request.site)

"""
Forms and formsets related to journals
"""
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField
from django.utils.translation import ugettext_lazy as _


class UsersJournalAccessForm(forms.Form):
    """
    Form to give access for a journal to multiple users.
    """
    expiration_date = DateField(
        required=True,
        widget=AdminDateWidget,
    )
    bulk_upload_csv = forms.FileField(
        required=True,
        label=_("Users' CSV file"),
        help_text=_(".csv file with single column consists of only usernames"),
    )


from django import forms
from django.utils.translation import ugettext as _


class UsersJournalAccessForm(forms.Form):
    """
    Form to give access for a journal to multiple users.
    """

    expiration_date = forms.DateField(
        required=True,
        widget=forms.widgets.DateInput(format="%d/%m/%Y"),
        help_text=_(
            "Date format should be DD/MM/YYYY"
        ),
    )

    bulk_upload_csv = forms.FileField(
        label=_(
            "Users' CSV file"
        ),
        required=True,
        help_text=_(
            ".csv file with usernames and first row should the heading with username."
        ),
    )


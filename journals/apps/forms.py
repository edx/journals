
from django import forms
from journals.models import Journal


class ImportUserCSVForm(forms.Form):
    class Meta:
        model = Journal
        fields = (
            "name",
            "slug",
            "active",
            "site",
            "catalog",
            "enable_data_sharing_consent",
            "enforce_data_sharing_consent",
            "enable_audit_enrollment",
            "enable_audit_data_reporting",
            "replace_sensitive_sso_username",
            "hide_course_original_price",
        )

    class Media:
        js = ('enterprise/admin/enterprise_customer.js', )

    def __init__(self, *args, **kwargs):
        """
        Initialize the form.

        Substitute a ChoiceField in for the catalog field that would
        normally be set up as a plain number entry field.
        """
        super(EnterpriseCustomerAdminForm, self).__init__(*args, **kwargs)

        self.fields['catalog'] = forms.ChoiceField(
            choices=self.get_catalog_options(),
            required=False,
            # pylint: disable=bad-continuation
            help_text='<a id="catalog-details-link" href="#" target="_blank" '
                      'data-url-template="{catalog_admin_change_url}"> View catalog details.</a>'
                      ' <p style="margin-top:-4px;"><a href="{catalog_admin_add_url}"'
                      ' target="_blank">Create a new catalog</a></p>'.format(
                catalog_admin_change_url=utils.get_catalog_admin_url_template(mode='change'),
                catalog_admin_add_url=utils.get_catalog_admin_url_template(mode='add'))
        )


    csv_file = forms.FileField()
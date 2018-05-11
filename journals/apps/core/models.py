""" Core models. """
from urllib.parse import urljoin

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from edx_rest_api_client.client import EdxRestApiClient
from jsonfield.fields import JSONField


class User(AbstractUser):
    """Custom user model for use with OpenID Connect."""
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True, null=True)

    @property
    def access_token(self):
        """ Returns an OAuth2 access token for this user, if one exists; otherwise None.

        Assumes user has authenticated at least once with edX Open ID Connect.
        """
        try:
            return self.social_auth.first().extra_data[u'access_token']
        except Exception:  # pylint: disable=broad-except
            return None

    class Meta(object):
        get_latest_by = 'date_joined'
        db_table = 'journals_user'

    def get_full_name(self):
        return self.full_name or super(User, self).get_full_name()

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.username)


class SiteConfiguration(models.Model):
    """
    Each site/tenant should have an instance of this model. This model is responsible for
    providing databased-backed configuration specific to each site.
    """

    site = models.OneToOneField('wagtailcore.Site', null=False, blank=False, on_delete=models.CASCADE)

    lms_url_root = models.URLField(
        verbose_name=_('LMS base url'),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=False,
        blank=False
    )

    lms_public_url_root_override = models.URLField(
        verbose_name=_('LMS public base url'),
        help_text=_(
            "Root public URL of this site's LMS. Only used for overwriting client-side URLs"
        ),
        null=True,
        blank=True
    )

    discovery_api_url = models.URLField(
        verbose_name=_('Discovery API URL'),
        null=False,
        blank=False,
    )

    discovery_journal_api_url = models.URLField(
        verbose_name=_('Discovery API URL for Journal Endpoint'),
        null=False,
        blank=False,
    )

    ecommerce_api_url = models.URLField(
        verbose_name=_('Ecommerce API URL'),
        null=False,
        blank=False,
    )

    ecommerce_journal_api_url = models.URLField(
        verbose_name=_('Ecommerce API URL for Journal Endpoint'),
        null=False,
        blank=False,
    )

    ecommerce_public_url_root = models.URLField(
        verbose_name=_('Ecommerce public base url'),
        null=True,
        blank=True
    )

    oauth_settings = JSONField(
        verbose_name=_('OAuth settings'),
        help_text=_('JSON string containing OAuth backend settings.'),
        null=False,
        blank=False,
        default={
            "SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY":"",
            "SOCIAL_AUTH_EDX_OIDC_SECRET":"",
            "SOCIAL_AUTH_EDX_OIDC_URL_ROOT":"",
            "SOCIAL_AUTH_EDX_OIDC_ISSUER":"",
            "SOCIAL_AUTH_EDX_OIDC_KEY":"",
            "SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT":"",
            "SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL":"",
            "SOCIAL_AUTH_EDX_OIDC_ISSUERS":[""]
        }
    )

    discovery_partner_id = models.CharField(
        max_length=8,
        verbose_name=_('Discovery service partner short code'),
        help_text=_('The short code of the associated Partner in discovery service (core_partners table)'),
        null=False,
        blank=False
    )

    ecommerce_partner_id = models.CharField(
        max_length=8,
        verbose_name=_('Ecommerce sevice partner short code'),
        help_text=_('The short code of the associated Partner in ecommerce service (partner_partners table)'),
        null=False,
        blank=False
    )

    currency_codes = models.CharField(
        max_length=256,
        verbose_name=_('Currencies supported for purchase'),
        help_text=_('Comma separated list of currency codes (from discovery core_currencies table)'),
        null=False,
        blank=False,
        default='USD'
    )

    def build_lms_url(self, path=''):
        """
        Returns path joined with the appropriate LMS URL root for the current site.

        Returns:
            str
        """
        return urljoin(self.lms_url_root, path)

    @property
    def oauth2_provider_url(self):
        """ Returns the URL for the OAuth 2.0 provider. """
        return self.build_lms_url('/oauth2')

    @property
    def access_token(self):
        """ Returns an access token for this site's service user.

        The access token is retrieved using the current site's OAuth credentials and the client credentials grant.
        The token is cached for the lifetime of the token, as specified by the OAuth provider's response. The token
        type is JWT.

        Returns:
            str: JWT access token
        """

        url = '{root}/access_token'.format(root=self.oauth2_provider_url)
        access_token, expiration_datetime = EdxRestApiClient.get_oauth_access_token(  # pylint: disable=unused-variable
            url,
            self.oauth_settings['SOCIAL_AUTH_EDX_OIDC_KEY'],
            self.oauth_settings['SOCIAL_AUTH_EDX_OIDC_SECRET'],
            token_type='jwt'
        )
        return access_token

    @property
    def lms_courses_api_client(self):
        """
        Returns an API client to the LMS courses API
        """
        return EdxRestApiClient(self.build_lms_url('/api/courses/v1/'), jwt=self.access_token)

    @property
    def discovery_api_client(self):
        """
        Returns an API client to access the Discovery service.
        """
        return EdxRestApiClient(self.discovery_api_url, jwt=self.access_token)

    @property
    def discovery_journal_api_client(self):
        """
        Returns an API client to access the Discovery service journal endpoint.
        """
        return EdxRestApiClient(self.discovery_journal_api_url, jwt=self.access_token)

    @property
    def ecommerce_api_client(self):
        """
        Returns an API client to access the Ecommerce service.
        """
        return EdxRestApiClient(self.ecommerce_api_url, jwt=self.access_token)

    @property
    def ecommerce_journal_api_client(self):
        """
        Returns an API client to access the Ecommerce journal endpoint.
        """
        return EdxRestApiClient(self.ecommerce_journal_api_url, jwt=self.access_token)

    def __str__(self):
        return str(self.site.site_name)  # pylint: disable=no-member

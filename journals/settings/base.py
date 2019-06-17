'''Common settings and globals'''
import os
import platform
from os.path import join, abspath, dirname
from logging.handlers import SysLogHandler


# PATH vars
def here(*x): return join(abspath(dirname(__file__)), *x)


PROJECT_ROOT = here("..")


def root(*x): return join(abspath(PROJECT_ROOT), *x)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('JOURNALS_SECRET_KEY', 'insecure-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'modelcluster',
    'release_util',
    'taggit',
)

THIRD_PARTY_APPS = (
    'rest_framework',
    'social_django',
    'waffle',
    'django_filters',
    'corsheaders',
    'storages'
)

PROJECT_APPS = (
    'journals.apps.core',
    'journals.apps.api',
    'journals.apps.journals',
    'journals.apps.search',
    'journals.apps.theming'
)

WAGTAIL_APPS = (
    'wagtail.api.v2',
    'wagtail.wagtailforms',
    'wagtail.wagtailredirects',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsites',
    'wagtail.wagtailusers',
    'wagtail.wagtailsnippets',
    'wagtail.wagtaildocs',
    'wagtail.wagtailimages',
    'wagtail.wagtailsearch',
    'wagtail.wagtailadmin',
    'wagtail.wagtailcore',
    'wagtail.contrib.modeladmin',
    'wagtail.contrib.settings',
)

INSTALLED_APPS += THIRD_PARTY_APPS
INSTALLED_APPS += PROJECT_APPS
INSTALLED_APPS += WAGTAIL_APPS

MIDDLEWARE_CLASSES = (
    'journals.apps.core.middleware.SettingsOverrideMiddleware',
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    'edx_django_utils.cache.middleware.TieredCacheMiddleware',
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',
)

ROOT_URLCONF = 'journals.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'journals.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# Set this value in the environment-specific files (e.g. local.py, production.py, test.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'journals',
        'USER': 'journ001',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'ATOMIC_REQUESTS': False,
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (
    root('conf', 'locale'),
)


# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = root('media')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

MEDIA_STORAGE_BACKEND = {
    'DEFAULT_FILE_STORAGE': 'django.core.files.storage.FileSystemStorage',
    'MEDIA_ROOT': MEDIA_ROOT,
    'MEDIA_URL': MEDIA_URL
}
# END MEDIA CONFIGURATION


# STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = root('assets')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    root('static'),
)

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': (
            root('templates'),
        ),
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'journals.apps.core.context_processors.core',
                'wagtail.contrib.settings.context_processors.settings',
            ),
            'debug': True,  # Django will only display debug pages if the global DEBUG setting is set to True.
        }
    },
]
# END TEMPLATE CONFIGURATION


# COOKIE CONFIGURATION
# The purpose of customizing the cookie names is to avoid conflicts when
# multiple Django services are running behind the same hostname.
# Detailed information at: https://docs.djangoproject.com/en/dev/ref/settings/
SESSION_COOKIE_NAME = 'journals_sessionid'
CSRF_COOKIE_NAME = 'journals_csrftoken'
LANGUAGE_COOKIE_NAME = 'journals_language'
# END COOKIE CONFIGURATION

# AUTHENTICATION CONFIGURATION
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'

AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = (
    'auth_backends.backends.EdXOpenIdConnect',
    'django.contrib.auth.backends.ModelBackend',
)

ENABLE_AUTO_AUTH = False
AUTO_AUTH_USERNAME_PREFIX = 'auto_auth_'

SOCIAL_AUTH_STRATEGY = 'journals.apps.social_auth.strategies.CurrentSiteDjangoStrategy'

# Request the user's permissions in the ID token
EXTRA_SCOPE = ['permissions']

# TODO Set this to another (non-staff, ideally) path.
LOGIN_REDIRECT_URL = '/'
# END AUTHENTICATION CONFIGURATION


# OPENEDX-SPECIFIC CONFIGURATION
PLATFORM_NAME = 'Your Platform Name Here'
# END OPENEDX-SPECIFIC CONFIGURATION

# Logging configuration
level = 'DEBUG' if DEBUG else 'INFO'
hostname = platform.node().split(".")[0]

# Use a different address for Mac OS X
syslog_address = '/var/run/syslog' if platform.system().lower() == 'darwin' else '/dev/log'
syslog_format = '[service_variant=journals][%(name)s] %(levelname)s [{hostname}  %(process)d] ' \
                '[%(pathname)s:%(lineno)d] - %(message)s'.format(hostname=hostname)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(process)d '
                      '[%(name)s] %(filename)s:%(lineno)d - %(message)s',
        },
        'syslog_format': {'format': syslog_format},
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'local': {
            'level': level,
            'class': 'logging.handlers.SysLogHandler',
            'address': syslog_address,
            'formatter': 'syslog_format',
            'facility': SysLogHandler.LOG_LOCAL0,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'local'],
            'propagate': True,
            'level': 'INFO'
        },
        'requests': {
            'handlers': ['console', 'local'],
            'propagate': True,
            'level': 'WARNING'
        },
        'factory': {
            'handlers': ['console', 'local'],
            'propagate': True,
            'level': 'WARNING'
        },
        'elasticsearch': {
            'handlers': ['console', 'local'],
            'propagate': True,
            'level': 'WARNING'
        },
        'django.request': {
            'handlers': ['console', 'local'],
            'propagate': True,
            'level': 'WARNING'
        },
        '': {
            'handlers': ['console', 'local'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'edx_rest_framework_extensions.auth.bearer.authentication.BearerAuthentication',
        'edx_rest_framework_extensions.auth.jwt.authentication.JwtAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

JWT_AUTH = {
    'JWT_ISSUER': [
        {
            'AUDIENCE': 'SET-ME-PLEASE',
            'ISSUER': 'http://127.0.0.1:8000/oauth2',
            'SECRET_KEY': 'SET-ME-PLEASE'
        }
    ],
    'JWT_PUBLIC_SIGNING_JWK_SET': None,
    'JWT_AUTH_COOKIE_HEADER_PAYLOAD': 'edx-jwt-cookie-header-payload',
    'JWT_AUTH_COOKIE_SIGNATURE': 'edx-jwt-cookie-signature',
    'JWT_AUTH_REFRESH_COOKIE': 'edx-jwt-refresh-cookie'
}
# Wagtail Specific

WAGTAIL_SITE_NAME = 'Journals'

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'journals.apps.search.backend',
        'URLS': ['http://journals.elasticsearch:9200'],
        'INDEX': 'journals',
        'TIMEOUT': 20,
        'OPTIONS': {'max_retries': 2, 'retry_on_timeout': True},
        'INDEX_SETTINGS': {},
    }
}

WAGTAILDOCS_DOCUMENT_MODEL = 'journals.JournalDocument'
WAGTAILIMAGES_IMAGE_MODEL = 'journals.JournalImage'
WAGTAIL_FRONTEND_LOGIN_URL = LOGIN_URL
WAGTAIL_ENABLE_UPDATE_CHECK = False

DEFAULT_FROM_EMAIL = "journals@edx.org"

THEME_DIR = '/edx/app/journals/themes/'

CSRF_COOKIE_NAME = 'journals_csrftoken'

ALLOWED_DOCUMENT_TYPES = ['application/pdf']
ALLOWED_DOCUMENT_FILE_EXTENSIONS = ['.pdf']

BATCH_SIZE_FOR_LMS_USER_API = 50
MAX_ELASTICSEARCH_UPLOAD_SIZE = 10000000  # maximum number of bytes per document that can be uploaded to elasticsearch

ELASTICSEARCH_URL = 'http://127.0.0.1:9500'
ELASTICSEARCH_INDEX_NAME = 'journals'

DEFAULT_PARTNER_ID = 1

AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'

EMAIL_BACKEND = 'django_ses.SESBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

PUBLISHER_FROM_EMAIL = None

OPENEXCHANGERATES_API_KEY = ''

PARLER_DEFAULT_LANGUAGE_CODE = 'en'
PARLER_LANGUAGES = {
    '1': [{'code': 'en'}],
    'default': {
        'fallbacks': ['en'],
        'hide_untranslated': 'False'
    }
}

CSRF_COOKIE_SECURE = False

SOCIAL_AUTH_EDX_OIDC_KEY = 'journals-key'
SOCIAL_AUTH_EDX_OIDC_SECRET = 'journals-secret'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = 'http://127.0.0.1:8000/oauth2'
SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL = 'http://127.0.0.1:8000/logout'
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = 'journals-secret'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT = 'http://127.0.0.1:8000/oauth2'
SOCIAL_AUTH_EDX_OIDC_ISSUER = 'http://127.0.0.1:8000/oauth2'
SOCIAL_AUTH_EDX_OAUTH2_KEY = 'journals-sso-key'
SOCIAL_AUTH_EDX_OAUTH2_SECRET = 'journals-sso-secret'
SOCIAL_AUTH_EDX_OAUTH2_ISSUER = 'http://127.0.0.1:8000'
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = 'http://127.0.0.1:8000'
SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL = 'http://127.0.0.1:8000/logout'

BACKEND_SERVICE_EDX_OAUTH2_KEY = 'journals-backend-service-key'
BACKEND_SERVICE_EDX_OAUTH2_SECRET = 'journals-service-secret'
BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = 'http://127.0.0.1:8000/oauth2'

API_ROOT = None

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

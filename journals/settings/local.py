from journals.settings.base import *

DEBUG = True

# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION

# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'journals',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'journals.mysql',
        'PORT': '3306',
    }
}
# END DATABASE CONFIGURATION

# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# END EMAIL CONFIGURATION

# TOOLBAR CONFIGURATION
# See: http://django-debug-toolbar.readthedocs.org/en/latest/installation.html
if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
    INSTALLED_APPS += (
        'debug_toolbar',
    )

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

INTERNAL_IPS = ('127.0.0.1',)
# END TOOLBAR CONFIGURATION

# AUTHENTICATION
# Use a non-SSL URL for authorization redirects
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

ENABLE_AUTO_AUTH = True

#####################################################################
# Lastly, see if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    from .private import *  # pylint: disable=import-error

# Set these to the correct values for your OAuth2/OpenID Connect provider (e.g., devstack)
SOCIAL_AUTH_EDX_OIDC_KEY = 'f777745993ea7b132c1d'
SOCIAL_AUTH_EDX_OIDC_SECRET = '7170a1689d15b288138265c95e8d7618cf63be16'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = 'http://edx.devstack.lms:18000/oauth2'
SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT = 'http://localhost:18000/oauth2'
SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL = 'http://localhost:18000/logout'
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = SOCIAL_AUTH_EDX_OIDC_SECRET
SOCIAL_AUTH_EDX_OIDC_ISSUER = 'http://edx.devstack.lms:18000/oauth2'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

LMS_BASE_INTERNAL_URL = 'http://edx.devstack.lms:18000'  # E.g. "http://edx.devstack.lms:18000
LMS_EXTERNAL_DOMAIN = 'localhost:18000'  # E.g. "http://localhost:18000
LMS_CLIENT_ID = 'UkNO3wRM207JnoVFF0UPIQWmHAAlpipXsVK5ofEH'  # Obtained through api-admin interface
LMS_CLIENT_SECRET = 'hpSUa3JviKkAFCFJKnHQt5aZ7setPe8QugTnuTzwKRSW4MhXkT60fXUWMrdZTkIvgE32Ny4bmXo56F4ztuWdI7dunaQfajfFZ248RYpaI05lQCeJ54ayTW3Djfm4nnVT'  # Obtained through api-admin interface
LMS_BLOCK_API_PATH = '/api/courses/v1/blocks/'  # E.g. "/api/courses/v1/blocks/"
DEFAULT_VIDEO_COURSE_RUN_ID = 'course-v1:edX%2BDemoX%2BDemo_Course'   # E.g. course-v1:edX%2BDemoX%2BDemo_Course

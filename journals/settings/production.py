from os import environ
import yaml

from journals.settings.base import *
from journals.settings.utils import get_env_setting


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

LOGGING['handlers']['local']['level'] = 'INFO'

# Keep track of the names of settings that represent dicts. Instead of overriding the values in base.py,
# the values read from disk should UPDATE the pre-configured dicts.
DICT_UPDATE_KEYS = ('JWT_AUTH',)

# This may be overridden by the YAML in JOURNALS_CFG, but it should be here as a default.
MEDIA_STORAGE_BACKEND = {}

CONFIG_FILE = get_env_setting('JOURNALS_CFG')

with open(CONFIG_FILE, encoding='utf-8') as f:
    config_from_yaml = yaml.load(f)

    # Remove the items that should be used to update dicts, and apply them separately rather
    # than pumping them into the local vars.
    dict_updates = {key: config_from_yaml.pop(key, None) for key in DICT_UPDATE_KEYS}

    for key, value in dict_updates.items():
        if value:
            vars()[key].update(value)

    vars().update(config_from_yaml)
    vars().update(MEDIA_STORAGE_BACKEND)

if 'EXTRA_APPS' in locals():
    INSTALLED_APPS += EXTRA_APPS

DB_OVERRIDES = dict(
    PASSWORD=environ.get('DB_MIGRATION_PASS', DATABASES['default']['PASSWORD']),
    ENGINE=environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
)

WAGTAILSEARCH_BACKENDS['default'].update({
    'URLS': [ELASTICSEARCH_URL],
    'INDEX_NAME': ELASTICSEARCH_INDEX_NAME,
})

for override, value in DB_OVERRIDES.items():
    DATABASES['default'][override] = value

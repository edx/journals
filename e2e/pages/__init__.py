import os

# Get the URL of the instance under test
BOK_CHOY_HOSTNAME = os.environ.get('BOK_CHOY_JOURNALS_HOSTNAME', 'journals.app')
BOK_CHOY_PORT = os.environ.get('BOK_CHOY_JOURNALS_PORT', 18606)
BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(BOK_CHOY_HOSTNAME, BOK_CHOY_PORT))

"""
Utility methods for journals
"""
import csv
import datetime
import hashlib
import logging
import waffle
from urllib.parse import urljoin, urlparse
import six

from wagtail.wagtailadmin import messages

logger = logging.getLogger(__name__)

BLOCK_SPAN_ID_FORMATTER = '{block_type}-{block_id}'
DISABLE_LMS_WAFFLE_SWITCH = 'disable_lms_integration'

def make_md5_hash(value):
    if value:
        value = str(value).encode('utf-8')
        return hashlib.md5(value).hexdigest()
    return value


def get_span_id(block_type, block_id):
    """
    Args:
        block_type: e:g "image", "doc" or "xblock_video" etc
        block_id: Id of searched object for example Id of JournalDocument or Video or Image object

    Returns: block fragment identifier e.g "image-c81e728d9d4c2f636f067f89cc14862c"
    """
    return BLOCK_SPAN_ID_FORMATTER.format(block_type=block_type, block_id=make_md5_hash(block_id))


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...

    Example:
        >>> get_cache_key(site_domain="example.com", resource="enterprise-learner")
        # Here is key format for above call
        # "site_domain:example.com__resource:enterprise-learner"
        a54349175618ff1659dee0978e3149ca

    Arguments:
        **kwargs: Key word arguments that need to be present in cache key.

    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join(['{}:{}'.format(item, value) for item, value in six.iteritems(kwargs)])
    return hashlib.md5(key.encode('utf-8')).hexdigest()


def get_image_url(site, image, rendition='original'):
    """
    Get image url for a given rendition, defaults to 'original'
    Args:
        image: the source Image object
        rendition: image rendition to return, None will fetch the original image url
    """
    if rendition:
        image_url = image.get_rendition(rendition).file.url
    else:
        image_url = image.file.url

    is_absolute_url = bool(urlparse(image_url).netloc)
    if is_absolute_url:
        return image_url
    else:
        return urljoin(site.root_url, image_url)


def add_messages(request, message_type, messages_list):
    """
        add messages of message type (success, error or warning etc) to render is template
    """
    message_adder = getattr(messages, message_type)
    for message in messages_list:
        if message:
            message_adder(request, message)


def get_default_expiration_date(journal):
    """
    Returns the default expiration date for journal access.
    """
    expiration_date = ""
    if journal:
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=journal.access_length)
    return expiration_date


def parse_csv(file_stream):
    """
    Parse csv file and return a list containing all the usernames.
    Arguments:
         file_stream: input file
    Yields:
        list: CSV line parsed into a list.
    """
    csv_file = csv.reader(file_stream.read().decode('utf-8').splitlines())
    for row in csv_file:
        yield row[0]


def delete_block_references(instance, block_type):
    """
    Removes reference of the given instance (JournalImage/JournalDocument)
    from their related journal pages. It deletes the related block from
    journal_page's body
    """
    from journals.apps.journals.blocks import (
        IMAGE_BLOCK_TYPE,
        PDF_BLOCK_TYPE,
        STREAM_DATA_DOC_FIELD
    )
    journal_pages = instance.get_journal_page_usage()
    for journal_page in journal_pages:
        has_changed = False
        journal_page_body = journal_page.body
        for body_index, data in enumerate(journal_page_body.stream_data):
            if block_type == PDF_BLOCK_TYPE and find_block(PDF_BLOCK_TYPE, STREAM_DATA_DOC_FIELD, data, instance) or \
                    block_type == IMAGE_BLOCK_TYPE and find_block(IMAGE_BLOCK_TYPE, IMAGE_BLOCK_TYPE, data, instance):
                        journal_page_body.stream_data.pop(body_index)
                        has_changed = True
        if has_changed:
            journal_page.save()
            journal_page.save_revision().publish()


def find_block(block_type, block_id_field, data, instance):
    from journals.apps.journals.blocks import STREAM_DATA_TYPE_FIELD
    return (data.get(STREAM_DATA_TYPE_FIELD, None) == block_type and
            instance.id == data.get('value').get(block_id_field))


def lms_integration_enabled():
    return not waffle.switch_is_active(DISABLE_LMS_WAFFLE_SWITCH)

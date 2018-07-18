"""
Utility methods for journals
"""
import hashlib
import six


def make_md5_hash(value):
    if value:
        value = str(value).encode('utf-8')
        return hashlib.md5(value).hexdigest()
    return value


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
    print('key=', key)
    return hashlib.md5(key.encode('utf-8')).hexdigest()


def get_image_url(image, rendition='original'):
    """
    Get image url for a given rendition, defaults to 'original'
    Args:
        image: the source Image object
        rendition: image rendition to return, None will fetch the original image url
    """
    if rendition:
        return image.get_rendition(rendition).file.url
    else:
        return image.file.url

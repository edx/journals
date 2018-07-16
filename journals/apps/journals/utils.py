"""
Utility methods for journals
"""
import hashlib


def make_md5_hash(value):
    if value:
        value = str(value).encode('utf-8')
        return hashlib.md5(value).hexdigest()
    return value

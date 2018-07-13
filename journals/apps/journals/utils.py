"""
Utility methods for journals
"""
import hashlib


def make_md5_hash(value):
    if value:
        value = str(value)
        return hashlib.md5(value.encode('utf-8')).hexdigest()
    else:
        return value

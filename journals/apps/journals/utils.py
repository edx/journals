""" Utils function for journal app. """

import unicodecsv
import datetime

from django.core.exceptions import ValidationError
from .models import Journal, JournalAccess
from journals.apps.core.models import User


def get_default_expiration_date(journal):
    """
    Returns the default expiration date for journal access.
    """
    expiration_date = ""
    if journal:
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=journal.access_length)
    return expiration_date


def get_object(class_name, attribute_name, attribute_value):
    """
    Returns the object if it exists otherwise None
    """
    try:
        obj = class_name.objects.get(**{attribute_name: attribute_value})
    except class_name.DoesNotExist:
        obj = None
    return obj


def create_journal_access(usernames, journal_id, expiration_date):
    """
    Creates the JournalAccess objects with given arguments.
    Arguments:
         usernames: set of unique usernames
         journal_id: id for journal on which we have to give access to users.
         expiration_date: expiration date for journal_access
    """
    journal = get_object(Journal, 'id', journal_id)
    for username in usernames:
        user = get_object(User, 'username', username)
        if user:
            JournalAccess.create_journal_access(user, journal, expiration_date)


def parse_csv(file_stream, expected_columns=None):
    """
    Parse csv file and return a stream of dictionaries representing each row.

    First line of CSV file must contain column headers.

    Arguments:
         file_stream: input file
         expected_columns (set[unicode]): columns that are expected to be present

    Yields:
        dict: CSV line parsed into a dictionary.
    """
    reader = unicodecsv.DictReader(file_stream, encoding="utf-8")

    if expected_columns and set(expected_columns) - set(reader.fieldnames):
        raise ValidationError("Expected column for username does not exist.")
    for row in reader:
        yield row

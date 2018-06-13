# -*- coding: utf-8 -*-
"""
Tests for custom blocks
"""
import ddt
from django.test import TestCase

from journals.apps.journals.blocks import JournalRawHTMLBlock


@ddt.ddt
class TestJournalRawHTMLBlock(TestCase):
    """
    Tests for JournalRawHTMLBlock
    """
    def setUp(self):
        super(TestJournalRawHTMLBlock, self).setUp()
        self.block = JournalRawHTMLBlock()

    @ddt.data(
        ('', ''),
        ('<h1>Heading</h1><p>First Paragraph</p>', '<h1>Heading</h1><p>First Paragraph</p>'),
        ('<p>First Paragraph</p><script>alert("Test")</script>', '<p>First Paragraph</p>'),
        (
                '<p>First Paragraph</p>'
                '<script>alert("Test")</script>'
                '<script src="http://example.com" />',
                '<p>First Paragraph</p>'
        ),
        (
                '<p>First Paragraph</p>'
                '<script>alert("Test")</script>'
                '<frame src="http://example.com" />',
                '<p>First Paragraph</p>'
        ),
        ('<p>First Paragraph</p><iframe src="http://example.com" />', '<p>First Paragraph</p>'),
        ('<p>First Paragraph</p><link rel="stylesheet" type="text/css" href="test.css" />', '<p>First Paragraph</p>'),
    )
    @ddt.unpack
    def test_value_for_form(self, given_value, transformed_value):
        """
        Test value of this block is properly cleaned before being saved
        """
        self.assertEqual(self.block.value_for_form(given_value), transformed_value)

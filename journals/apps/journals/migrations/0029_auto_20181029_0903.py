# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-29 09:03
from __future__ import unicode_literals

from django.db import migrations
import journals.apps.journals.models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0028_remove_existing_userpagevisits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journalaboutpage',
            name='custom_content',
            field=journals.apps.journals.models.JournalRichTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='journalindexpage',
            name='intro',
            field=journals.apps.journals.models.JournalRichTextField(blank=True),
        ),
    ]

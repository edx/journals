# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-08-06 14:50
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('journals', '0019_auto_20180730_2129'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text=None, through='taggit.TaggedItem', to='taggit.Tag', verbose_name='tags'),
        ),
    ]

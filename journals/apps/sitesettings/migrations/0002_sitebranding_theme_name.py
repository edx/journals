# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-02 15:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesettings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitebranding',
            name='theme_name',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-15 00:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0028_auto_20160514_1742'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job',
            old_name='distance',
            new_name='trip_distance',
        ),
    ]

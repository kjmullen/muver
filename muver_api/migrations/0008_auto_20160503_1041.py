# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-03 17:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0007_auto_20160502_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='destination_a',
            field=models.CharField(default='', max_length=80),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='job',
            name='destination_b',
            field=models.CharField(default='', max_length=80),
            preserve_default=False,
        ),
    ]

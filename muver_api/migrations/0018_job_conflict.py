# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-12 00:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0017_userprofile_banned'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='conflict',
            field=models.BooleanField(default=False),
        ),
    ]
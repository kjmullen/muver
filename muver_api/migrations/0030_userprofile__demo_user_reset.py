# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-16 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0029_auto_20160514_1745'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='_demo_user_reset',
            field=models.BooleanField(default=False),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-06 00:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0013_auto_20160505_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='distance',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
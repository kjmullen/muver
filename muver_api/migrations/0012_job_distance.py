# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-04 20:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('muver_api', '0011_job_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='distance',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-16 09:46
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='creation_date',
            field=models.DateField(auto_now_add=True, default=datetime.datetime(2016, 4, 16, 9, 46, 5, 868417, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='word',
            name='downvotes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='word',
            name='standard',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='word',
            name='upvotes',
            field=models.IntegerField(default=0),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-11 21:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_profile_max_suggest_words_per_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlanguage',
            name='is_moderator',
            field=models.BooleanField(default=False),
        ),
    ]

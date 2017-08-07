# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-05 10:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20170731_2153'),
        ('word', '0004_auto_20170731_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('place', models.CharField(max_length=150)),
                ('submitter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Profile')),
                ('word', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='word.Word')),
            ],
        ),
    ]
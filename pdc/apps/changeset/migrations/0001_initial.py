# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Change',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_class', models.CharField(max_length=200)),
                ('target_id', models.PositiveIntegerField()),
                ('old_value', models.TextField()),
                ('new_value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Changeset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('committed_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

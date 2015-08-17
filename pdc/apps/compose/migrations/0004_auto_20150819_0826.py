#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0003_auto_20150610_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='composeimage',
            name='path',
            field=models.ForeignKey(to='compose.Path', null=True),
        ),
        migrations.AlterField(
            model_name='path',
            name='path',
            field=models.CharField(unique=True, max_length=4096, blank=True),
        ),
    ]

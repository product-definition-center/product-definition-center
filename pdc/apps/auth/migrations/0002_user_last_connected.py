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
        ('kerb_auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_connected',
            field=models.DateTimeField(null=True, verbose_name='date last connected to service', blank=True),
        ),
    ]

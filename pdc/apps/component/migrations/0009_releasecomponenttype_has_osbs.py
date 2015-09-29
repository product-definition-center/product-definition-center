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
        ('component', '0008_auto_20150914_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='releasecomponenttype',
            name='has_osbs',
            field=models.BooleanField(default=False),
        ),
    ]

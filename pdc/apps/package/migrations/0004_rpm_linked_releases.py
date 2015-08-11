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
        ('release', '0002_auto_20150512_0719'),
        ('package', '0003_buildimage_releases'),
    ]

    operations = [
        migrations.AddField(
            model_name='rpm',
            name='linked_releases',
            field=models.ManyToManyField(related_name='linked_rpms', to='release.Release'),
        ),
    ]

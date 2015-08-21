# -*- coding: utf-8 -*-
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
        ('compose', '0005_auto_20150819_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='composeimage',
            name='path',
            field=models.ForeignKey(to='compose.Path'),
        ),
    ]

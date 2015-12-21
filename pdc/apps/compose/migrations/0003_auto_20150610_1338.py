# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import pdc.apps.compose.models


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0002_auto_20150512_0707'),
    ]

    operations = [
        migrations.AddField(
            model_name='variantarch',
            name='rtt_testing_status',
            field=models.ForeignKey(default=pdc.apps.compose.models.ComposeAcceptanceTestingState.get_untested, to='compose.ComposeAcceptanceTestingState'),
        ),
        migrations.AlterField(
            model_name='compose',
            name='acceptance_testing',
            field=models.ForeignKey(default=pdc.apps.compose.models.ComposeAcceptanceTestingState.get_untested, to='compose.ComposeAcceptanceTestingState'),
        ),
    ]

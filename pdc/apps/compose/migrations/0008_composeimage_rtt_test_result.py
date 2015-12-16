# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pdc.apps.compose.models


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0007_auto_20151120_0336'),
    ]

    operations = [
        migrations.AddField(
            model_name='composeimage',
            name='rtt_test_result',
            field=models.ForeignKey(default=pdc.apps.compose.models.ComposeAcceptanceTestingState.get_untested, to='compose.ComposeAcceptanceTestingState'),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0008_composeimage_rtt_test_result'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='composetree',
            unique_together=set([('compose', 'variant', 'arch', 'location', 'scheme')]),
        ),
    ]

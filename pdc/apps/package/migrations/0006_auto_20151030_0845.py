# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0005_auto_20150907_0905'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='dependency',
            unique_together=set([]),
        ),
    ]

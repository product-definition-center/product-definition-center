# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0007_auto_20150821_0834'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='releasecomponent',
            unique_together=set([('release', 'name')]),
        ),
    ]

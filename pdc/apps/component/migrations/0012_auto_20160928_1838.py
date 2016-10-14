# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0011_auto_20151126_0602'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='releasecomponent',
            unique_together=set([('release', 'name', 'type')]),
        ),
    ]
